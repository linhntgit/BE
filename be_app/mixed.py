"""REML random-intercept GLS with observed-information Satterthwaite inference.

Two covariance components: subject(sequence) and residual. No external statistics
process or GUI state. Contrast df follow 2*v**2/(gradient' Cov(theta) gradient).
"""

import math

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize_scalar
from scipy.stats import f, t


def fit_random_intercept(y, x, subjects):
    y, x = np.asarray(y, dtype=float), np.asarray(x, dtype=float)
    n, p = x.shape
    if n <= p or np.linalg.matrix_rank(x) != p:
        raise ValueError("Mô hình thiếu bậc tự do hoặc ma trận thiết kế không đủ hạng.")
    subject = np.asarray(subjects)
    j = (subject[:, None] == subject[None, :]).astype(float)
    eye = np.eye(n)

    def profile(log_ratio):
        v = eye + math.exp(log_ratio) * j
        factor = cho_factor(v)
        inv = cho_solve(factor, eye)
        w = x.T @ inv @ x
        covariance = np.linalg.inv(w)
        beta = covariance @ x.T @ inv @ y
        residual = y - x @ beta
        scale = float(residual @ inv @ residual / (n - p))
        if scale <= 1e-16:
            raise ValueError("Phương sai suy biến.")
        objective = (n - p) * math.log(scale) + 2 * np.log(np.diag(factor[0])).sum() + np.linalg.slogdet(w)[1]
        return float(objective), scale, covariance, beta, inv

    fit = minimize_scalar(
        lambda value: profile(value)[0], bounds=(-24, 18), method="bounded", options={"xatol": 1e-11}
    )
    if not fit.success:
        raise ValueError("REML không hội tụ.")
    objective, residual_variance, _, _, _ = profile(float(fit.x))
    subject_variance = residual_variance * math.exp(float(fit.x))
    boundary = float(fit.x) < -20
    if boundary:
        subject_variance = 0.0
    v = residual_variance * eye + subject_variance * j
    inv = np.linalg.inv(v)
    covariance = np.linalg.inv(x.T @ inv @ x)
    beta = covariance @ x.T @ inv @ y
    projection = inv - inv @ x @ covariance @ x.T @ inv
    py = projection @ y
    components = [eye, j]
    hessian = np.array(
        [
            [
                float(-0.5 * np.trace(projection @ a @ projection @ b) + py @ a @ projection @ b @ py)
                for b in components
            ]
            for a in components
        ]
    )
    if boundary:
        parameter_covariance = np.array([[2 * residual_variance**2 / (n - p), 0.0], [0.0, 0.0]])
    elif np.linalg.eigvalsh(hessian).min() <= 0:
        raise ValueError("Hessian REML không xác định dương; không suy luận Satterthwaite.")
    else:
        parameter_covariance = np.linalg.inv(hessian)

    def contrast(weights, confidence=0.90):
        c = np.asarray(weights, dtype=float)
        estimate = float(c @ beta)
        variance = float(c @ covariance @ c)
        z = inv @ x @ covariance @ c
        gradient = np.array([z @ a @ z for a in components])
        denominator = float(gradient @ parameter_covariance @ gradient)
        if variance <= 0 or denominator <= 0:
            raise ValueError("Không ước tính được phương sai/bậc tự do contrast.")
        df = 2 * variance**2 / denominator
        se = math.sqrt(variance)
        critical = float(t.ppf((1 + confidence) / 2, df))
        statistic = estimate / se
        return dict(
            estimate=estimate,
            se=se,
            df=df,
            t=statistic,
            p=float(2 * t.sf(abs(statistic), df)),
            confidence=confidence,
            critical=critical,
            lower=estimate - critical * se,
            upper=estimate + critical * se,
        )

    residual = y - x @ beta
    logdet = float(np.linalg.slogdet(v)[1])
    reml = -0.5 * (
        (n - p) * math.log(2 * math.pi)
        + logdet
        + np.linalg.slogdet(x.T @ inv @ x)[1]
        + float(residual @ inv @ residual)
    )
    # Fixed-design normalization is used for comparing benchmark REML likelihoods.
    reml += 0.5 * float(np.linalg.slogdet(x.T @ x)[1])
    return dict(
        beta=beta,
        covariance=covariance,
        contrast=contrast,
        residual_variance=residual_variance,
        subject_variance=subject_variance,
        parameter_covariance=parameter_covariance,
        hessian_eigenvalues=np.linalg.eigvalsh(hessian).tolist(),
        predicted=(x @ beta).tolist(),
        residuals=residual.tolist(),
        reml_log_likelihood=reml,
        objective=objective,
        converged=True,
        boundary=boundary,
        n=n,
        p=p,
        x=x,
        y=y,
    )


def ols(y, x):
    y, x = np.asarray(y, dtype=float), np.asarray(x, dtype=float)
    n, p = x.shape
    if n <= p or np.linalg.matrix_rank(x) != p:
        raise ValueError("ANOVA thiếu bậc tự do hoặc ma trận không đủ hạng.")
    covariance = np.linalg.inv(x.T @ x)
    beta = covariance @ x.T @ y
    residual = y - x @ beta
    sse = float(residual @ residual)
    mse = sse / (n - p)
    leverage = np.sum((x @ covariance) * x, axis=1)
    residual_diagnostics = []
    for observed, predicted, error, h in zip(y, x @ beta, residual, leverage, strict=True):
        denominator = mse * (1 - h)
        studentized = float(error / math.sqrt(denominator)) if denominator > 1e-16 else None
        residual_diagnostics.append(
            dict(
                Observed=float(observed),
                Predicted=float(predicted),
                Residual=float(error),
                Leverage=float(h),
                Studentized_internal=studentized,
                Review_flag=bool(abs(studentized) > 3) if studentized is not None else False,
                Standardization="Internal OLS: residual / sqrt(MSE * (1 - leverage)); exploratory |r| > 3",
            )
        )
    return dict(
        beta=beta,
        covariance=covariance * mse,
        sse=sse,
        mse=mse,
        df=n - p,
        residuals=residual.tolist(),
        predicted=(x @ beta).tolist(),
        residual_diagnostics=residual_diagnostics,
    )


def ols_test(fit, weights):
    c = np.asarray(weights, dtype=float)
    estimate = float(c @ fit["beta"])
    variance = float(c @ fit["covariance"] @ c)
    if variance <= 1e-16:
        raise ValueError("Phương sai contrast suy biến.")
    statistic = estimate**2 / variance
    return dict(
        estimate=estimate,
        se=math.sqrt(variance),
        df=fit["df"],
        f=statistic,
        p=float(f.sf(statistic, 1, fit["df"])),
    )
