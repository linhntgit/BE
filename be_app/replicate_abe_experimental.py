"""Experimental full4 REML ABE; never imported by the production decision pipeline.

Specification: docs/FDA_REPLICATE_ABE_METHOD_SPEC.md. Every fit is diagnostic only,
including a numerically successful fit. No PASS/FAIL or release eligibility is returned.
"""

import math

import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from scipy.stats import t

from be_app.replicate import prepare_replicate

MODEL_ID = "EXPERIMENTAL_FULL4_FA0_REML_OBSERVED_SATTERTHWAITE_0.1"


class ReplicateLikelihood:
    """Negative REML likelihood in FA/log-residual coordinates; no expected outputs."""

    def __init__(self, data, endpoint):
        if not {"subject_id", "sequence", "period", "treatment", endpoint} <= set(data.columns):
            raise ValueError("Experimental full4 input is missing required columns.")
        normalized = data.copy()
        if normalized.subject_id.isna().any() or normalized.subject_id.map(str).str.strip().eq("").any():
            raise ValueError("Experimental full4 input has missing subject identifiers.")
        normalized["subject_id"] = normalized.subject_id.map(str)
        self.data = (
            prepare_replicate(normalized, endpoint, "full4")
            .sort_values(["subject_id", "period"], kind="stable")
            .reset_index(drop=True)
        )
        d = self.data
        if len(d) > 600:
            raise ValueError("Experimental prototype is limited to 600 observations.")
        self.y_offset = float(np.log(d[endpoint]).mean())
        self.y = np.log(d[endpoint].to_numpy()) - self.y_offset
        self.x = np.column_stack(
            [
                np.ones(len(d)),
                d.sequence.eq("TRTR"),
                *[d.period.eq(period) for period in (1, 2, 3)],
                d.treatment.eq("T"),
            ]
        ).astype(float)
        self.n, self.p = self.x.shape
        if self.n <= self.p or np.linalg.matrix_rank(self.x) != self.p:
            raise ValueError("Full4 fixed design is rank deficient.")
        subject = d.subject_id.to_numpy()
        same = (subject[:, None] == subject[None, :]).astype(float)
        ref = d.treatment.eq("R").to_numpy(float)
        test = d.treatment.eq("T").to_numpy(float)
        self.components = np.array(
            [
                same * np.outer(ref, ref),
                same * (np.outer(ref, test) + np.outer(test, ref)),
                same * np.outer(test, test),
                np.diag(ref),
                np.diag(test),
            ]
        )
        self.eye = np.eye(self.n)

    @staticmethod
    def transform(parameters):
        a, b, c, qr, qt = np.asarray(parameters, float)
        rr, rt = math.exp(qr), math.exp(qt)
        covariance = np.array([a * a, a * b, b * b + c * c, rr, rt])
        jacobian = np.array(
            [
                [2 * a, 0, 0, 0, 0],
                [b, a, 0, 0, 0],
                [0, 2 * b, 2 * c, 0, 0],
                [0, 0, 0, rr, 0],
                [0, 0, 0, 0, rt],
            ]
        )
        return covariance, jacobian

    def evaluate(self, parameters, information=False):
        theta, jacobian = self.transform(parameters)
        v = np.einsum("k,kij->ij", theta, self.components)
        factor = cho_factor(v, lower=True, check_finite=False)
        inv = cho_solve(factor, self.eye, check_finite=False)
        ux = inv @ self.x
        w = self.x.T @ ux
        fixed_covariance = np.linalg.inv(w)
        beta = fixed_covariance @ ux.T @ self.y
        projection = inv - ux @ fixed_covariance @ ux.T
        py = projection @ self.y
        objective = 0.5 * (2 * np.log(np.diag(factor[0])).sum() + np.linalg.slogdet(w)[1] + self.y @ py)
        score = np.array([0.5 * (np.sum(projection * a.T) - py @ a @ py) for a in self.components])
        gradient = jacobian.T @ score
        if not information:
            return float(objective), gradient
        pa = [projection @ a for a in self.components]
        ay = [a @ py for a in self.components]
        raw_information = np.array(
            [
                [
                    -0.5 * np.sum(first * second.T) + one @ projection @ two
                    for second, two in zip(pa, ay, strict=True)
                ]
                for first, one in zip(pa, ay, strict=True)
            ]
        )
        hessian = jacobian.T @ raw_information @ jacobian
        # Nonlinear covariance curvature: essential at a rank-deficient G boundary.
        hessian[0, 0] += 2 * score[0]
        hessian[0, 1] += score[1]
        hessian[1, 0] += score[1]
        hessian[1, 1] += 2 * score[2]
        hessian[2, 2] += 2 * score[2]
        hessian[3, 3] += theta[3] * score[3]
        hessian[4, 4] += theta[4] * score[4]
        return dict(
            objective=float(objective),
            gradient=gradient,
            hessian=(hessian + hessian.T) / 2,
            covariance_parameters=theta,
            jacobian=jacobian,
            fixed_covariance=fixed_covariance,
            beta=beta,
            inv=inv,
            projection=projection,
        )

    def starts_and_bounds(self):
        # All starts come only from input observations and fixed design, never a reference fit.
        residual = self.y - self.x @ np.linalg.lstsq(self.x, self.y, rcond=None)[0]
        variance = float(residual @ residual / (self.n - self.p))
        if not math.isfinite(variance) or variance <= 1e-12:
            raise ValueError("Degenerate response variance; experimental fit not evaluated.")
        scale = math.sqrt(variance)
        starts = [
            np.array([a * scale, b * scale, c * scale, math.log(variance * r), math.log(variance * s)])
            for a, b, c, r, s in (
                (0.8, 0.5, 0.6, 0.4, 0.4),
                (0.8, 0.8, 0.0, 0.4, 0.4),
                (0.2, -0.3, 0.9, 0.8, 0.1),
                (0.8, -0.5, 0.6, 0.1, 0.8),
            )
        ]
        bounds = [(-10 * scale, 10 * scale)] * 3 + [(math.log(variance) - 20, math.log(variance) + 5)] * 2
        return starts, bounds


def fit_full_replicate_abe(data, endpoint, *, max_iterations=500):
    model = ReplicateLikelihood(data, endpoint)
    starts, bounds = model.starts_and_bounds()
    attempts = []
    solutions = []
    for start in starts:
        result = minimize(
            model.evaluate,
            start,
            jac=True,
            method="L-BFGS-B",
            bounds=bounds,
            options={"ftol": 1e-13, "gtol": 1e-7, "maxiter": max_iterations, "maxls": 40},
        )
        objective, gradient = model.evaluate(result.x)
        norm = float(np.linalg.norm(gradient, ord=np.inf))
        converged = bool(result.success and norm < 1e-4)
        attempts.append(
            dict(
                objective=objective,
                gradient_inf=norm,
                converged=converged,
                iterations=int(result.nit),
                message=str(result.message),
            )
        )
        if converged:
            solutions.append(result)
    if not solutions:
        raise ValueError("Experimental full4 REML did not converge to a stationary point.")
    lowest = min(float(result.fun) for result in solutions)
    # Objective differences at rounding noise are ties; prefer the more stationary fit.
    tied = [result for result in solutions if float(result.fun) <= lowest + 1e-9]
    best = min(tied, key=lambda result: float(np.linalg.norm(model.evaluate(result.x)[1], ord=np.inf)))
    fitted = model.evaluate(best.x, information=True)
    eigenvalues = np.linalg.eigvalsh(fitted["hessian"])
    if eigenvalues.min() <= 0 or eigenvalues.max() / eigenvalues.min() > 1e12:
        raise ValueError("Experimental observed Hessian is not stably positive definite.")
    theta = fitted["covariance_parameters"]
    g = np.array([[theta[0], theta[1]], [theta[1], theta[2]]])
    boundary = bool(np.linalg.eigvalsh(g).min() < max(np.linalg.eigvalsh(g).max(), 1e-12) * 1e-7)
    bound_hit = any(
        min(abs(x - low), abs(x - high)) < 1e-5 for x, (low, high) in zip(best.x, bounds, strict=True)
    )
    c = np.zeros(model.p)
    c[-1] = 1.0
    fixed_cov = fitted["fixed_covariance"]
    variance = float(c @ fixed_cov @ c)
    z = fitted["inv"] @ model.x @ fixed_cov @ c
    sensitivity = fitted["jacobian"].T @ np.array([z @ a @ z for a in model.components])
    denominator = float(sensitivity @ np.linalg.solve(fitted["hessian"], sensitivity))
    if variance <= 0 or denominator <= 0:
        raise ValueError("Experimental contrast variance/df not estimable.")
    df = 2 * variance**2 / denominator
    estimate = float(c @ fitted["beta"])
    se = math.sqrt(variance)
    critical = float(t.ppf(0.95, df))
    beta = fitted["beta"].copy()
    beta[0] += model.y_offset
    reml = -fitted["objective"] - 0.5 * (model.n - model.p) * math.log(2 * math.pi)
    reml += 0.5 * float(np.linalg.slogdet(model.x.T @ model.x)[1])
    return dict(
        model_id=MODEL_ID,
        status="EXPERIMENTAL_BOUNDARY" if boundary or bound_hit else "EXPERIMENTAL_FIT",
        inference_allowed=False,
        production_connected=False,
        boundary=boundary,
        optimizer_bound_hit=bound_hit,
        converged=True,
        optimizer_attempts=attempts,
        estimate=estimate,
        se=se,
        df=df,
        critical_t=critical,
        gmr=math.exp(estimate),
        ci90=[math.exp(estimate - critical * se), math.exp(estimate + critical * se)],
        random_covariance_order=["R", "T"],
        random_covariance=g.tolist(),
        residual_variance_r=float(theta[3]),
        residual_variance_t=float(theta[4]),
        fixed_parameter_labels=[
            "intercept_R_RTRT_period4",
            "sequence_TRTR",
            "period_1",
            "period_2",
            "period_3",
            "T_minus_R",
        ],
        fixed_parameters=beta.tolist(),
        fixed_covariance=fixed_cov.tolist(),
        reml_log_likelihood=reml,
        observed_hessian_eigenvalues=eigenvalues.tolist(),
        observed_hessian=fitted["hessian"].tolist(),
        fitted_parameters=best.x.tolist(),
        n_observations=model.n,
        n_subjects=int(model.data.subject_id.nunique()),
        population=model.data[["subject_id", "sequence", "period", "treatment"]].to_dict("records"),
    )
