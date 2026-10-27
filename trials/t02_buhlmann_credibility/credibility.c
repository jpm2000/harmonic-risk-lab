/*
 * credibility.c — Bühlmann credibility theory for insurance pricing.
 *
 * Source: Bühlmann (1967). "Experience rating and credibility."
 *         ASTIN Bulletin 4(3): 199–207.
 *         Bühlmann & Straub (1970). "Credibility for loss ratios."
 *
 * The credibility model blends an insured's own experience with a
 * collective prior: P_cred = Z * X_bar + (1-Z) * mu_prior.
 *
 * VERIFIED PROPERTIES (see hypothesis.md):
 *   1. credibility_z in [0,1]
 *   2. credibility_z is monotone increasing in n
 *   3. credibility_premium is a convex combination of its inputs
 *   4. credibility_premium is non-negative when both inputs >= 0
 */

#include <math.h>

/*
 * credibility_z — Bühlmann credibility factor.
 *
 *   Z = n / (n + k)
 *
 * n — number of observation years  (must be >= 0)
 * k — credibility parameter k = sigma_e^2 / sigma_u^2  (must be > 0)
 *
 * Returns: Z in [0, 1]
 * Returns: -1.0 for invalid inputs (k <= 0 or n < 0)
 *
 * PROPERTY 1: 0 <= credibility_z <= 1 for all valid inputs.
 * PROPERTY 2: credibility_z(n1, k) >= credibility_z(n2, k) when n1 >= n2 >= 0.
 */
double credibility_z(double n, double k) {
    if (n < 0.0 || k <= 0.0)
        return -1.0;
    return n / (n + k);
}

/*
 * credibility_premium — Bühlmann credibility-weighted premium.
 *
 *   P = Z * x_bar + (1 - Z) * mu_prior
 *
 * z         — credibility factor from credibility_z() (must be in [0, 1])
 * x_bar     — individual's observed average loss ratio (must be >= 0)
 * mu_prior  — collective prior (market-wide) expected loss ratio (must be >= 0)
 *
 * Returns: premium in [min(x_bar, mu_prior), max(x_bar, mu_prior)]
 * Returns: -1.0 for invalid inputs
 *
 * PROPERTY 3: min(x_bar, mu_prior) <= credibility_premium <= max(x_bar, mu_prior)
 *             when z in [0,1], x_bar >= 0, mu_prior >= 0.
 * PROPERTY 4: credibility_premium >= 0 when x_bar >= 0, mu_prior >= 0, z in [0,1].
 */
double credibility_premium(double z, double x_bar, double mu_prior) {
    if (z < 0.0 || z > 1.0 || x_bar < 0.0 || mu_prior < 0.0)
        return -1.0;
    return z * x_bar + (1.0 - z) * mu_prior;
}

/*
 * credibility_param_k — Estimate the Bühlmann k from variance components.
 *
 * Bühlmann's k = process_variance / structural_variance, where:
 *   process_variance  = E[Var(X | theta)]  (within-risk volatility)
 *   structural_variance = Var(E[X | theta]) (between-risk volatility)
 *
 * process_var    — estimate of expected within-risk variance  (must be >= 0)
 * structural_var — estimate of between-risk variance          (must be > 0)
 *
 * Returns: k = process_var / structural_var (always >= 0 for valid inputs)
 * Returns: -1.0 for invalid inputs
 *
 * PROPERTY: credibility_param_k >= 0 when process_var >= 0, structural_var > 0.
 */
double credibility_param_k(double process_var, double structural_var) {
    if (process_var < 0.0 || structural_var <= 0.0)
        return -1.0;
    return process_var / structural_var;
}

/*
 * full_credibility_n — Minimum sample size for "full credibility" at tolerance r.
 *
 * In classical credibility theory, the sample size for full credibility is:
 *   n* = (z_{alpha/2} / r)^2 * CV^2
 * where CV = coefficient of variation = sigma/mu of the loss distribution.
 *
 * z_alpha2 — z-score for (alpha/2) confidence (e.g., 1.96 for 95%)  (> 0)
 * r        — allowed relative error (e.g., 0.05 for 5%)              (must be in (0,1))
 * cv       — coefficient of variation of losses                       (must be >= 0)
 *
 * Returns: minimum n for full credibility (always >= 0 for valid inputs)
 * Returns: -1.0 for invalid inputs
 *
 * PROPERTY: full_credibility_n >= 0 for all valid inputs.
 */
double full_credibility_n(double z_alpha2, double r, double cv) {
    if (z_alpha2 <= 0.0 || r <= 0.0 || r >= 1.0 || cv < 0.0)
        return -1.0;
    double ratio = z_alpha2 / r;
    return ratio * ratio * cv * cv;
}
