/*
 * risk_model.c — Analytical market risk calculations
 *
 * Implements Value at Risk (VaR) and Expected Shortfall (CVaR) using
 * closed-form normal-distribution formulas, plus Basel III risk-weighted
 * asset (RWA) computation.
 *
 * These are the kinds of models that need to be FORMALLY CORRECT in
 * regulated environments (banking, mining, defense). Aristotle will
 * verify the mathematical invariants that regulators and auditors require.
 */

#include <math.h>

/*
 * portfolio_var — 1-day parametric Value at Risk at confidence level alpha.
 *
 * Inputs:
 *   mu      — expected daily portfolio return (any real number)
 *   sigma   — daily portfolio volatility  (must be >= 0)
 *   alpha   — confidence level, e.g. 0.95 for 95% VaR (must be in (0.5, 1.0))
 *   horizon — holding period in days (must be >= 1)
 *
 * Returns:
 *   VaR as a non-negative loss amount, floored at 0 if the distribution
 *   implies expected profit > downside risk.
 *
 * PROPERTY WE WANT TO PROVE:
 *   For all valid inputs (sigma >= 0, alpha in (0.5,1), horizon >= 1),
 *   portfolio_var returns a value >= 0.
 */
double portfolio_var(double mu, double sigma, double alpha, int horizon) {
    /* Approximate z-score for common confidence levels.
       A production model would use the inverse normal CDF (erfinv). */
    double z;
    if (alpha >= 0.99)       z = 2.326;
    else if (alpha >= 0.975) z = 1.960;
    else                     z = 1.645;  /* covers 95% and below */

    double scaled_sigma = sigma * sqrt((double)horizon);
    double scaled_mu    = mu    * (double)horizon;

    double raw_var = z * scaled_sigma - scaled_mu;
    return raw_var > 0.0 ? raw_var : 0.0;
}

/*
 * portfolio_es — Expected Shortfall (CVaR) at confidence level alpha.
 *
 * ES is the average loss in the worst (1-alpha) fraction of scenarios.
 * It is always >= VaR at the same confidence level (coherent risk measure).
 *
 * PROPERTY WE WANT TO PROVE:
 *   portfolio_es(mu, sigma, alpha, h) >= portfolio_var(mu, sigma, alpha, h)
 *   for all valid inputs.
 */
double portfolio_es(double mu, double sigma, double alpha, int horizon) {
    double var = portfolio_var(mu, sigma, alpha, horizon);

    /* For a normal distribution:
       ES = VaR + phi(z) / (1-alpha) * scaled_sigma
       phi(1.645) ≈ 0.1031  */
    double phi_z        = 0.1031;
    double scaled_sigma = sigma * sqrt((double)horizon);
    double es           = var + (phi_z / (1.0 - alpha)) * scaled_sigma;
    return es;
}

/*
 * calculate_rwa — Risk-Weighted Asset (Basel III simplified).
 *
 * exposure    — nominal monetary exposure (must be >= 0)
 * risk_weight — regulatory risk weight between 0.0 and 1.50
 *
 * Returns RWA = exposure * risk_weight, or -1.0 for invalid inputs.
 *
 * PROPERTY WE WANT TO PROVE:
 *   For exposure >= 0 and risk_weight in [0, 1.5],
 *   calculate_rwa returns a value in [0, exposure * 1.5].
 */
double calculate_rwa(double exposure, double risk_weight) {
    if (exposure < 0.0 || risk_weight < 0.0 || risk_weight > 1.5)
        return -1.0;
    return exposure * risk_weight;
}
