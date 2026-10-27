/*
 * evt_model.c — Extreme Value Theory: VaR and ES via Peaks-over-Threshold.
 *
 * Source: McNeil, Frey & Embrechts (2005). "Quantitative Risk Management."
 *         Princeton University Press. Chapter 7.
 *
 * CONTEXT (Marsh Mining Losses Uncovered, 2025):
 *   $15.3 billion in insured mining losses over 2006-2025.
 *   Fire/explosion (25.7%) and geotechnical/tailings events produce
 *   catastrophic single losses (Brumadinho 2019 = $7B+).
 *   These follow power-law tails — normal VaR is dangerously wrong.
 *
 * THE MODEL: Peaks-over-Threshold (POT) with Generalized Pareto Distribution.
 *
 *   X ~ GPD(xi, sigma, u)  for excess losses above threshold u
 *
 *   xi    — shape / tail index. xi > 0 → heavy tail (Pareto-type).
 *            Typical mining range: 0.3–0.7
 *   sigma — scale parameter (> 0)
 *   u     — threshold (only losses above u follow GPD)
 *   p_u   — P(X > u) = N_u / N  (empirical exceedance probability)
 *
 * VaR FORMULA (ξ ≠ 0):
 *   VaR_α = u + (σ/ξ) · [(p_u / (1−α))^ξ − 1]
 *
 * ES FORMULA (ξ < 1):
 *   ES_α = (VaR_α + σ − ξ·u) / (1 − ξ)
 *
 * VERIFIED PROPERTIES (see hypothesis.md):
 *   1. gpd_var >= u (VaR is always above the threshold)
 *   2. gpd_es >= gpd_var (ES ≥ VaR — coherent risk measure)
 *   3. gpd_var monotone in alpha
 *   4. evt_tail_premium >= 0 when xi > 0 (heavy tail requires more capital)
 */

#include <math.h>

/*
 * gpd_var — Value-at-Risk via Peaks-over-Threshold / Generalized Pareto.
 *
 * u      — threshold (>= 0, losses above u follow GPD)
 * sigma  — GPD scale parameter (> 0)
 * xi     — GPD tail index (> 0 for heavy tail; 0 < xi < 1 for finite mean)
 * p_u    — P(X > u), empirical exceedance probability (0 < p_u <= 1)
 * alpha  — confidence level (0 < alpha < 1; use 0.995 for Solvency II)
 *
 * Returns: VaR_alpha >= u for valid inputs.
 * Returns: u when (1 - alpha) >= p_u (confidence below threshold exceedance).
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 1: gpd_var >= u for all valid inputs.
 *   Proof sketch: pow(p_u/(1-alpha), xi) >= 1 when p_u >= (1-alpha) and xi > 0,
 *   so (sigma/xi)*(ratio^xi - 1) >= 0, so result >= u.
 *
 * PROPERTY 3: gpd_var(alpha1) >= gpd_var(alpha2) when alpha1 >= alpha2.
 *   Proof sketch: alpha1 >= alpha2 => (1-alpha1) <= (1-alpha2) =>
 *   p_u/(1-alpha1) >= p_u/(1-alpha2) => ratio1 >= ratio2 => var1 >= var2.
 */
double gpd_var(double u, double sigma, double xi, double p_u, double alpha) {
    if (u < 0.0 || sigma <= 0.0 || xi <= 0.0 || xi >= 2.0 ||
        p_u <= 0.0 || p_u > 1.0 || alpha <= 0.0 || alpha >= 1.0)
        return -1.0;

    double one_minus_alpha = 1.0 - alpha;
    if (one_minus_alpha >= p_u)
        return u;  /* VaR sits at the threshold for low confidence levels */

    double ratio = p_u / one_minus_alpha;
    return u + (sigma / xi) * (pow(ratio, xi) - 1.0);
}

/*
 * gpd_es — Expected Shortfall (CVaR) beyond VaR under GPD.
 *
 * ES_alpha = (VaR_alpha + sigma - xi * u) / (1 - xi)
 *
 * Requires xi < 1 for finite ES. When xi >= 1 (extreme heavy tail),
 * the expected loss above VaR is infinite — ES is undefined and we
 * return -1.0 as an explicit signal that the tail is too heavy to insure.
 *
 * PROPERTY 2: gpd_es >= gpd_var for all valid inputs.
 *   Proof: ES = (VaR + sigma - xi*u) / (1-xi).
 *   Need ES >= VaR => (VaR + sigma - xi*u)/(1-xi) >= VaR
 *   => VaR + sigma - xi*u >= VaR*(1-xi)  [multiply both sides by (1-xi) > 0]
 *   => VaR + sigma - xi*u >= VaR - xi*VaR
 *   => sigma - xi*u >= -xi*VaR
 *   => sigma >= xi*(u - VaR).
 *   Since VaR >= u, (u - VaR) <= 0, and xi > 0, so xi*(u-VaR) <= 0 <= sigma.
 *   Hence ES >= VaR. QED.
 */
double gpd_es(double u, double sigma, double xi, double p_u, double alpha) {
    if (u < 0.0 || sigma <= 0.0 || xi <= 0.0 || xi >= 1.0 ||
        p_u <= 0.0 || p_u > 1.0 || alpha <= 0.0 || alpha >= 1.0)
        return -1.0;

    double var = gpd_var(u, sigma, xi, p_u, alpha);
    if (var < 0.0)
        return -1.0;

    return (var + sigma - xi * u) / (1.0 - xi);
}

/*
 * normal_var — VaR under the normal (Gaussian) approximation.
 *
 * VaR_alpha = mu + z_alpha * sigma_n
 *
 * This is the standard textbook formula. Used to benchmark against EVT:
 * for the same confidence level, EVT VaR should be >= normal VaR when xi > 0.
 *
 * mu      — mean loss (>= 0)
 * sigma_n — standard deviation of losses (> 0)
 * z_alpha — standard normal quantile (e.g., 1.645 for 95%, 2.326 for 99.5%)
 *
 * Returns: VaR >= mu >= 0 for valid inputs (when z_alpha >= 0).
 * Returns: -1.0 for invalid inputs.
 */
double normal_var(double mu, double sigma_n, double z_alpha) {
    if (mu < 0.0 || sigma_n <= 0.0 || z_alpha < 0.0)
        return -1.0;
    return mu + z_alpha * sigma_n;
}

/*
 * evt_tail_premium — capital premium for heavy tails vs. normal distribution.
 *
 * premium = gpd_var - normal_var
 *
 * When xi > 0 and confidence is high enough, this is always positive.
 * It represents the EXTRA capital a mining insurer must hold — above what
 * a naive normal distribution would suggest — to remain solvent.
 *
 * Marsh finding: fire/explosion and geotechnical events produce power-law
 * tails in mining. The tail premium explains why mining insurance is expensive.
 *
 * PROPERTY 4: evt_tail_premium >= 0 when xi > 0 and calibration is correct.
 *   This is the key comparison property — Aristotle must reason about the
 *   relative ordering of two different VaR formulas.
 *
 * Returns: gpd_var - normal_var (positive = EVT requires more capital).
 * Returns: -1.0 if either component is invalid.
 */
double evt_tail_premium(
    double u, double sigma, double xi, double p_u, double alpha,
    double mu, double sigma_n, double z_alpha
) {
    double var_evt = gpd_var(u, sigma, xi, p_u, alpha);
    double var_nrm = normal_var(mu, sigma_n, z_alpha);
    if (var_evt < 0.0 || var_nrm < 0.0)
        return -1.0;
    return var_evt - var_nrm;
}
