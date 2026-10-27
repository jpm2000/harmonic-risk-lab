/*
 * insurance_model.c — Actuarial premium pricing principles
 *
 * Implements three standard premium calculation principles:
 *   1. Expected Value Principle
 *   2. Standard Deviation Principle
 *   3. Variance Principle
 * Plus an excess-of-loss (XL) reinsurance layer pricer using Pareto tails.
 *
 * These are the core pricing functions for an insurance broker system.
 * Aristotle will formally verify that premiums always satisfy the
 * "no underpricing" invariant: premium >= expected loss.
 */

#include <math.h>

/*
 * premium_ev — Expected Value Principle.
 *
 *   P = (1 + theta) * E[L]
 *
 * theta        — relative safety loading (must be > 0, e.g. 0.20 = 20%)
 * expected_loss — E[L] (must be >= 0)
 *
 * PROPERTY WE WANT TO PROVE:
 *   For expected_loss >= 0 and theta > 0,
 *   premium_ev returns a value strictly greater than expected_loss.
 *   (i.e., the insurer always charges more than expected cost.)
 */
double premium_ev(double expected_loss, double theta) {
    if (expected_loss < 0.0 || theta <= 0.0)
        return -1.0;  /* invalid inputs */
    return (1.0 + theta) * expected_loss;
}

/*
 * premium_sd — Standard Deviation Principle.
 *
 *   P = E[L] + k * sigma(L)
 *
 * k         — safety loading per unit of volatility (must be > 0)
 * std_loss  — standard deviation of losses (must be >= 0)
 *
 * PROPERTY WE WANT TO PROVE:
 *   For std_loss >= 0 and k > 0,
 *   premium_sd >= expected_loss.
 */
double premium_sd(double expected_loss, double std_loss, double k) {
    if (expected_loss < 0.0 || std_loss < 0.0 || k <= 0.0)
        return -1.0;
    return expected_loss + k * std_loss;
}

/*
 * premium_variance — Variance Principle.
 *
 *   P = E[L] + beta * Var(L)
 *
 * beta         — variance loading (must be > 0)
 * variance_loss — Var[L] = sigma^2 (must be >= 0)
 *
 * PROPERTY WE WANT TO PROVE:
 *   premium_variance >= expected_loss for valid inputs.
 */
double premium_variance(double expected_loss, double variance_loss, double beta) {
    if (expected_loss < 0.0 || variance_loss < 0.0 || beta <= 0.0)
        return -1.0;
    return expected_loss + beta * variance_loss;
}

/*
 * layer_expected_loss — Expected loss for an XL reinsurance layer [R, R+L].
 *
 * Assumes Pareto-distributed ground-up losses (common for heavy-tailed
 * catastrophe and mining liability exposures).
 *
 * retention   — attachment point R (must be >= x_m)
 * limit       — layer width L (must be > 0)
 * alpha_pareto — Pareto tail index (must be > 1 for finite mean)
 * x_m         — Pareto scale (minimum loss, must be > 0)
 *
 * PROPERTY WE WANT TO PROVE:
 *   layer_expected_loss >= 0 for all valid inputs, and
 *   layer_expected_loss <= limit (the layer can't expect more than its cap).
 */
double layer_expected_loss(double retention, double limit,
                           double alpha_pareto, double x_m) {
    if (retention < x_m || limit <= 0.0 || alpha_pareto <= 1.0 || x_m <= 0.0)
        return -1.0;

    /* Pareto limited expected value: LEV(d) = E[min(L, d)] for L ~ Pareto(a, xm)
       For d >= xm: LEV(d) = xm/(a-1) * [1 - (xm/d)^(a-1)]
       Layer EL = LEV(retention + limit) - LEV(retention)  */
    double a  = alpha_pareto;
    double xm = x_m;

    double lev_top = (xm / (a - 1.0)) * (1.0 - pow(xm / (retention + limit), a - 1.0));
    double lev_ret = (xm / (a - 1.0)) * (1.0 - pow(xm / retention,           a - 1.0));

    double el = lev_top - lev_ret;
    return el > 0.0 ? el : 0.0;
}
