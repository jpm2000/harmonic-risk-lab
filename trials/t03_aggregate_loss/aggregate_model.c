/*
 * aggregate_model.c — Compound Poisson aggregate loss formulas.
 *
 * Source: Curriculum Module 4 (Collective Risk Model)
 *         Loss Data Analytics, Chapter 3 (Aggregate Loss Models)
 *
 * THE MODEL:  S = X₁ + X₂ + ... + Xₙ
 *   N ~ Poisson(lambda)    frequency
 *   Xᵢ ~ F_severity       each claim size (iid, independent of N)
 *
 * CLOSED-FORM IDENTITIES (what Aristotle will verify):
 *   E[S]    = lambda * mean_x
 *   Var(S)  = lambda * (var_x + mean_x²)   [compound Poisson identity]
 *           = lambda * ex2                  [where ex2 = E[X²]]
 *
 * These C functions implement the formulas exactly.
 * The Python simulator (numerics/aggregate_simulation.py) uses the same
 * formulas as a sanity check on its Monte Carlo results.
 *
 * VERIFIED PROPERTIES (see hypothesis.md):
 *   1. aggregate_mean ≥ 0 for valid inputs
 *   2. aggregate_variance ≥ 0 for valid inputs
 *   3. aggregate_variance = lambda * (var_x + mean_x²)  [identity]
 *   4. aggregate_std_dev ≥ 0
 *   5. aggregate_cvar ≥ aggregate_var at same confidence level
 */

#include <math.h>

/*
 * aggregate_mean — E[S] = lambda * mean_x
 *
 * lambda  — Poisson frequency parameter (expected claims per year, >= 0)
 * mean_x  — expected individual claim size (>= 0)
 *
 * Returns: E[S] >= 0  for valid inputs.
 * Returns: -1.0 if either input is negative.
 *
 * PROPERTY 1: aggregate_mean >= 0 when lambda >= 0 and mean_x >= 0.
 */
double aggregate_mean(double lambda, double mean_x) {
    if (lambda < 0.0 || mean_x < 0.0)
        return -1.0;
    return lambda * mean_x;
}

/*
 * aggregate_variance — Var(S) = lambda * (var_x + mean_x²)
 *
 * This is the compound Poisson variance identity.
 * It combines the within-claim variability (var_x) and the variability
 * of having more/fewer claims (mean_x² weighted by lambda).
 *
 * lambda  — Poisson lambda (>= 0)
 * var_x   — Var(X) = variance of individual claims (>= 0)
 * mean_x  — E[X] (>= 0)
 *
 * Returns: Var(S) >= 0  for valid inputs.
 *
 * PROPERTY 2: aggregate_variance >= 0 when lambda >= 0, var_x >= 0, mean_x >= 0.
 * PROPERTY 3: aggregate_variance = lambda * (var_x + mean_x * mean_x).
 *             [compound Poisson identity — verified algebraically by Aristotle]
 */
double aggregate_variance(double lambda, double var_x, double mean_x) {
    if (lambda < 0.0 || var_x < 0.0 || mean_x < 0.0)
        return -1.0;
    return lambda * (var_x + mean_x * mean_x);
}

/*
 * aggregate_std_dev — standard deviation of S = sqrt(Var(S))
 *
 * Returns: sqrt of aggregate variance (>= 0 by construction).
 *
 * PROPERTY 4: aggregate_std_dev >= 0 for valid inputs.
 */
double aggregate_std_dev(double lambda, double var_x, double mean_x) {
    double var = aggregate_variance(lambda, var_x, mean_x);
    if (var < 0.0)
        return -1.0;    /* propagate sentinel */
    return sqrt(var);
}

/*
 * aggregate_coefficient_of_variation — CV(S) = std(S) / E[S]
 *
 * The CV measures relative dispersion. For the compound Poisson model:
 *   CV(S) = sqrt(E[X²]) / (sqrt(lambda) * E[X])
 *
 * Used to compare risk across portfolios of different sizes.
 *
 * Returns: CV >= 0 when E[S] > 0.
 * Returns: -1.0 if E[S] = 0 or inputs are invalid.
 *
 * PROPERTY 5: aggregate_cv >= 0 when lambda > 0, mean_x > 0, var_x >= 0.
 */
double aggregate_cv(double lambda, double var_x, double mean_x) {
    if (lambda <= 0.0 || mean_x <= 0.0 || var_x < 0.0)
        return -1.0;
    double es   = aggregate_mean(lambda, mean_x);
    double std  = aggregate_std_dev(lambda, var_x, mean_x);
    return std / es;
}

/*
 * aggregate_var_normal_approx — VaR of S using normal approximation.
 *
 * By the Central Limit Theorem, for large lambda,
 *   S ≈ Normal(E[S], Var(S))
 * so: VaR_alpha(S) ≈ E[S] + z_alpha * sqrt(Var(S))
 *
 * This is the parametric VaR formula applied to aggregate losses.
 *
 * lambda   — Poisson lambda (>= 0)
 * var_x    — Var(X)        (>= 0)
 * mean_x   — E[X]          (>= 0)
 * z_alpha  — z-score for confidence level (> 0; e.g., 2.326 for 99.5%)
 *
 * Returns: VaR >= E[S] >= 0 for valid inputs.
 *
 * PROPERTY 6: aggregate_var_normal_approx >= aggregate_mean(lambda, mean_x)
 *             when z_alpha >= 0.
 * PROPERTY 7: aggregate_var_normal_approx >= 0 when all inputs are valid.
 */
double aggregate_var_normal_approx(
    double lambda, double var_x, double mean_x, double z_alpha
) {
    if (lambda < 0.0 || var_x < 0.0 || mean_x < 0.0 || z_alpha < 0.0)
        return -1.0;
    double es  = aggregate_mean(lambda, mean_x);
    double std = aggregate_std_dev(lambda, var_x, mean_x);
    return es + z_alpha * std;
}

/*
 * aggregate_cvar_normal_approx — CVaR of S using normal approximation.
 *
 * For S ~ Normal(mu, sigma²):
 *   CVaR_alpha(S) = mu + sigma * phi(z_alpha) / (1 - alpha)
 *
 * where phi is the standard normal PDF, z_alpha is the alpha-quantile.
 *
 * This is always >= VaR at the same alpha (coherence property, ES >= VaR).
 *
 * phi_z_alpha — value of the standard normal PDF at z_alpha
 *               (e.g., phi(2.326) ≈ 0.0267 for 99.5%)
 * one_minus_alpha — 1 - alpha (e.g., 0.005 for 99.5%)
 *
 * PROPERTY 8: aggregate_cvar_normal_approx >= aggregate_var_normal_approx
 *             for the same inputs (ES >= VaR, coherent risk measure property).
 */
double aggregate_cvar_normal_approx(
    double lambda, double var_x, double mean_x,
    double z_alpha, double phi_z_alpha, double one_minus_alpha
) {
    if (lambda < 0.0 || var_x < 0.0 || mean_x < 0.0 ||
        z_alpha < 0.0 || phi_z_alpha < 0.0 || one_minus_alpha <= 0.0)
        return -1.0;
    double es  = aggregate_mean(lambda, mean_x);
    double std = aggregate_std_dev(lambda, var_x, mean_x);
    return es + std * (phi_z_alpha / one_minus_alpha);
}
