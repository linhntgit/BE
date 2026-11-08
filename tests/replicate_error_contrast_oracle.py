"""Independent numerical REML reference for an INTERIOR synthetic test only.

No imports from be_app. Uses orthonormal error contrasts, linear covariance
coordinates, derivative-free optimization and finite-difference information.
It is deliberately outside the application and does not implement release policy.
"""

import math

import numpy as np
from scipy.linalg import block_diag, null_space
from scipy.optimize import minimize
from scipy.stats import t


def finite_derivatives(function, point, steps):
    base = function(point)
    n = len(point)
    gradient, hessian = np.zeros(n), np.zeros((n, n))
    for i in range(n):
        di = np.eye(n)[i] * steps[i]
        positive, negative = function(point + di), function(point - di)
        gradient[i] = (positive - negative) / (2 * steps[i])
        hessian[i, i] = (positive - 2 * base + negative) / steps[i] ** 2
        for j in range(i):
            dj = np.eye(n)[j] * steps[j]
            hessian[i, j] = hessian[j, i] = (
                function(point + di + dj) - function(point + di - dj)
                - function(point - di + dj) + function(point - di - dj)
            ) / (4 * steps[i] * steps[j])
    return gradient, hessian


def fit_error_contrasts(data):
    # Different coding: baseline TRTR, period 1, T; contrast is minus R coefficient.
    data = data.sort_values(["subject_id", "period"])
    x = np.column_stack([
        np.ones(len(data)), data.sequence.eq("RTRT"),
        *[data.period.eq(p) for p in (2, 3, 4)], data.treatment.eq("R"),
    ]).astype(float)
    y = np.log(data.cmax.to_numpy())
    q = null_space(x.T)
    response = q.T @ y
    blocks = []
    for _, block in data.groupby("subject_id", sort=True):
        ref = block.treatment.eq("R").to_numpy(float)
        test = 1 - ref
        blocks.append([
            np.outer(ref, ref), np.outer(ref, test) + np.outer(test, ref),
            np.outer(test, test), np.diag(ref), np.diag(test),
        ])
    components = np.array([block_diag(*[b[k] for b in blocks]) for k in range(5)])
    restricted = np.array([q.T @ a @ q for a in components])

    def objective(theta):
        gr, gt, tt, rr, rt = theta
        if min(gr, tt, rr, rt) <= 0 or gr * tt <= gt**2:
            return 1e20
        covariance = np.einsum("k,kij->ij", theta, restricted)
        sign, logdet = np.linalg.slogdet(covariance)
        if sign <= 0:
            return 1e20
        return 0.5 * (logdet + response @ np.linalg.solve(covariance, response))

    # Start scale derived from data, independent of the prototype/reference answers.
    residual = y - x @ np.linalg.lstsq(x, y, rcond=None)[0]
    scale = residual @ residual / (len(y) - x.shape[1])
    initial = scale * np.array([0.5, 0.0, 0.5, 0.5, 0.5])
    result = minimize(objective, initial, method="Nelder-Mead", options={
        "maxiter": 5000, "xatol": 1e-10, "fatol": 1e-10,
    })
    if not result.success:
        raise ValueError("Independent error-contrast optimizer failed")
    theta = result.x
    steps = np.maximum(abs(theta), 0.01) * 2e-4
    gradient, hessian = finite_derivatives(objective, theta, steps)
    if np.linalg.norm(gradient, ord=np.inf) > 1e-3 or np.linalg.eigvalsh(hessian).min() <= 0:
        raise ValueError("Independent numerical information/score failed")

    def gls(parameters):
        covariance = np.einsum("k,kij->ij", parameters, components)
        vx, vy = np.linalg.solve(covariance, x), np.linalg.solve(covariance, y)
        fixed_covariance = np.linalg.inv(x.T @ vx)
        beta = fixed_covariance @ x.T @ vy
        return -beta[-1], fixed_covariance[-1, -1]

    estimate, variance = gls(theta)
    sensitivity = finite_derivatives(lambda parameters: gls(parameters)[1], theta, steps)[0]
    df = 2 * variance**2 / (sensitivity @ np.linalg.solve(hessian, sensitivity))
    se = math.sqrt(variance)
    critical = t.ppf(0.95, df)
    return dict(
        covariance=theta, estimate=estimate, se=se, df=df,
        ci90=np.exp([estimate - critical * se, estimate + critical * se]),
        random_eigenvalues=np.linalg.eigvalsh([[theta[0], theta[1]], [theta[1], theta[2]]]),
        hessian_eigenvalues=np.linalg.eigvalsh(hessian), gradient_inf=np.max(abs(gradient)),
    )
