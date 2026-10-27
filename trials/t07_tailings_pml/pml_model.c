/*
 * pml_model.c — Probable Maximum Loss for tailings dam / catastrophic events.
 *
 * Source: McNeil, Frey & Embrechts (2005). "Quantitative Risk Management." Ch. 7.
 *         Pickands (1975). "Statistical inference using extreme order statistics."
 *
 * REAL-WORLD CALIBRATION (Marsh data):
 *   2015 Fundão tailings dam (Samarco, Mariana, Brazil) — billions in losses.
 *   2019 Brumadinho dam disaster — $7B+ settlement with Brazilian authorities.
 *   Tailings = ~0.7% of Marsh event count but some of the largest single losses.
 *   This is the definition of rare + catastrophic: infrequent but portfolio-defining.
 *
 * THE MODEL: Pareto-distributed severity + return period framework.
 *
 *   Pareto survival function:
 *     P(X > x) = (x_m / x)^alpha    for x >= x_m > 0, alpha > 0
 *
 *   Probable Maximum Loss for return period T:
 *     PML(T) = x_m * T^(1/alpha)
 *
 *   Annual Exceedance Probability (AEP) for loss level x:
 *     AEP(x) = (x_m / x)^alpha = P(X > x)
 *
 * VERIFIED PROPERTIES (see hypothesis.md):
 *   1. pml_pareto >= x_m for T >= 1 (PML exceeds minimum loss)
 *   2. pml_pareto monotone in T (longer return period = larger event)
 *   3. aep_pareto monotone decreasing in x (bigger losses are rarer)
 *   4. aep_pareto ∈ (0, 1] for valid inputs
 *   5. aep(pml(T)) = 1/T (inverse consistency)
 *   6. pml_pareto monotone decreasing in alpha (heavier tail = larger events)
 */

#include <math.h>

/*
 * pml_pareto — Probable Maximum Loss for a Pareto-severity event.
 *
 * PML(T) = x_m * T^(1/alpha)
 *
 * x_m   — minimum loss / scale (> 0, USD)
 * alpha — Pareto tail index (> 0; smaller alpha = heavier tail)
 *         Typical tailings events: alpha ≈ 1.2–1.5
 * T     — return period in years (>= 1)
 *
 * Returns: PML >= x_m for T >= 1.
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 1: pml_pareto >= x_m.
 *   Proof: T >= 1 => T^(1/alpha) >= 1 (since 1/alpha > 0). So x_m*T^(1/alpha) >= x_m. QED.
 *
 * PROPERTY 2: monotone in T.
 *   pml_pareto(T1) >= pml_pareto(T2) when T1 >= T2 >= 1.
 *   Proof: T1 >= T2 >= 1, 1/alpha > 0 => T1^(1/alpha) >= T2^(1/alpha). QED.
 *
 * PROPERTY 6: monotone decreasing in alpha.
 *   pml_pareto(alpha1, T) <= pml_pareto(alpha2, T) when alpha1 >= alpha2 > 0.
 *   Proof: alpha1 >= alpha2 => 1/alpha1 <= 1/alpha2. For T >= 1:
 *   T^(1/alpha1) <= T^(1/alpha2). So x_m*T^(1/alpha1) <= x_m*T^(1/alpha2). QED.
 */
double pml_pareto(double x_m, double alpha, double T) {
    if (x_m <= 0.0 || alpha <= 0.0 || T < 1.0)
        return -1.0;
    return x_m * pow(T, 1.0 / alpha);
}

/*
 * aep_pareto — Annual Exceedance Probability for a Pareto-distributed loss.
 *
 * AEP(x) = P(X > x) = (x_m / x)^alpha
 *
 * This is the probability that, in any given year, the loss exceeds `x`.
 * AEP = 0.01 means the 1-in-100-year event.
 * AEP = 0.005 means the 1-in-200-year event (Solvency II SCR standard).
 *
 * x     — loss level to evaluate (>= x_m)
 * x_m   — minimum loss / scale (> 0)
 * alpha — Pareto tail index (> 0)
 *
 * Returns: AEP ∈ (0, 1] for valid inputs (x >= x_m).
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 3: aep_pareto monotone decreasing in x.
 *   aep_pareto(x1,...) <= aep_pareto(x2,...) when x1 >= x2 >= x_m.
 *   Proof: x1 >= x2 => x_m/x1 <= x_m/x2 (ratios). Raising positive ratio
 *   to power alpha > 0 preserves order. So (x_m/x1)^alpha <= (x_m/x2)^alpha. QED.
 *
 * PROPERTY 4: aep_pareto ∈ (0, 1] for x >= x_m > 0.
 *   Proof: x >= x_m > 0 => x_m/x ∈ (0, 1]. (x_m/x)^alpha ∈ (0, 1] for alpha > 0. QED.
 */
double aep_pareto(double x, double x_m, double alpha) {
    if (x <= 0.0 || x_m <= 0.0 || alpha <= 0.0 || x < x_m)
        return -1.0;
    return pow(x_m / x, alpha);
}

/*
 * return_period — return period T for a given loss level x.
 *
 * T = 1 / AEP(x) = (x / x_m)^alpha
 *
 * A loss of x is expected once every T years.
 *
 * Returns: T >= 1 for x >= x_m (always at least 1 year return period).
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY: return_period >= 1 for x >= x_m.
 *   Proof: x >= x_m => x/x_m >= 1 => (x/x_m)^alpha >= 1 for alpha > 0. QED.
 */
double return_period(double x, double x_m, double alpha) {
    if (x <= 0.0 || x_m <= 0.0 || alpha <= 0.0 || x < x_m)
        return -1.0;
    return pow(x / x_m, alpha);
}

/*
 * pml_consistency_check — verifies PML and AEP are consistent inverses.
 *
 * aep(pml(T)) should equal 1/T.
 *
 * This function computes aep(pml_pareto(x_m, alpha, T)) and returns
 * how close it is to 1/T. A well-implemented model returns 0.0 (exact).
 *
 * Returns: |aep(pml(T)) - 1/T| — should be 0 (or floating-point epsilon).
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 5: pml_consistency_check returns 0.0 for all valid inputs.
 *   This is the definitional consistency: the return period of the T-year PML is T.
 */
double pml_consistency_check(double x_m, double alpha, double T) {
    if (x_m <= 0.0 || alpha <= 0.0 || T < 1.0)
        return -1.0;
    double pml  = pml_pareto(x_m, alpha, T);
    double aep  = aep_pareto(pml, x_m, alpha);
    double expected = 1.0 / T;
    double diff = aep - expected;
    return diff < 0.0 ? -diff : diff;  /* absolute value without math.h fabs */
}
