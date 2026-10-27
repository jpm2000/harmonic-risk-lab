/*
 * concentration_model.c — Single point of failure / production concentration risk.
 *
 * Source: Marsh "Mining Losses Uncovered" (2025).
 * Patrick Walker, Rio Tinto: "Dependence on complex, interconnected equipment
 * amplifies the impact of single-point failures. The industry's shift toward
 * single, high-capacity machines has aggravated this exposure."
 *
 * Machinery breakdown = 16.5% of $15.3B mining losses (2006-2025).
 * BI share for machinery breakdown > 82% (above the 80% overall average).
 *
 * THE MODEL:
 *   f             — concentration fraction: share of output from one asset (0 < f <= 1)
 *   daily_revenue — total daily production revenue (>= 0)
 *   recovery_days — days to restore the failed asset (>= 0)
 *   n_machines    — number of identical machines sharing the load equally (>= 1)
 *
 *   concentrated_bi  = f * daily_revenue * recovery_days
 *   diversified_bi   = (1/n) * daily_revenue * recovery_days
 *
 * DIVERSIFICATION PRINCIPLE:
 *   n = 1 (one machine):      bi_loss = daily_revenue * recovery_days   (max exposure)
 *   n = 2 (two equal mills):  bi_loss = 0.5 * daily_revenue * recovery_days
 *   n = 4 (four equal mills): bi_loss = 0.25 * daily_revenue * recovery_days
 *
 * VERIFIED PROPERTIES (see hypothesis.md):
 *   1. concentrated_bi_loss >= 0
 *   2. concentrated_bi_loss monotone in f
 *   3. concentrated_bi_loss monotone in recovery_days
 *   4. diversified_bi_loss(n) <= concentrated_bi_loss(1.0)
 *   5. diversified_bi_loss monotone decreasing in n_machines
 *   6. concentration_premium >= 0
 */

#include <math.h>

/*
 * concentrated_bi_loss — BI loss from failure of one asset handling fraction f.
 *
 * f             — fraction of output from this asset (0 < f <= 1.0)
 * daily_revenue — total daily revenue of the operation (>= 0)
 * recovery_days — days to restore this asset (>= 0)
 *
 * Returns: f * daily_revenue * recovery_days >= 0.
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 1: concentrated_bi_loss >= 0 for f > 0, daily_revenue >= 0, recovery_days >= 0.
 *
 * PROPERTY 2: monotone in f.
 *   concentrated_bi_loss(f1,...) >= concentrated_bi_loss(f2,...) when f1 >= f2.
 *   Proof: result = f * rev * days. f1 >= f2 >= 0 and rev,days >= 0
 *   => f1*rev*days >= f2*rev*days. QED.
 *
 * PROPERTY 3: monotone in recovery_days.
 *   Proof: result = f * rev * days. days1 >= days2 >= 0 and f,rev >= 0
 *   => f*rev*days1 >= f*rev*days2. QED.
 */
double concentrated_bi_loss(double f, double daily_revenue, double recovery_days) {
    if (f <= 0.0 || f > 1.0 || daily_revenue < 0.0 || recovery_days < 0.0)
        return -1.0;
    return f * daily_revenue * recovery_days;
}

/*
 * diversified_bi_loss — BI loss when production is split across n equal machines.
 *
 * If one of n identical machines fails, production drops by fraction 1/n.
 *
 * n_machines    — number of machines sharing load equally (>= 1)
 * daily_revenue — total daily revenue (>= 0)
 * recovery_days — days to restore the failed machine (>= 0)
 *
 * Returns: (1/n) * daily_revenue * recovery_days.
 * Returns: -1.0 for invalid inputs (n < 1).
 *
 * PROPERTY 4: diversified_bi_loss(n,...) <= concentrated_bi_loss(1.0,...).
 *   Proof: 1/n <= 1.0 for n >= 1. So (1/n)*rev*days <= 1.0*rev*days. QED.
 *
 * PROPERTY 5: monotone decreasing in n_machines.
 *   diversified_bi_loss(n1,...) <= diversified_bi_loss(n2,...) when n1 >= n2 >= 1.
 *   Proof: n1 >= n2 >= 1 => 1/n1 <= 1/n2 => (1/n1)*rev*days <= (1/n2)*rev*days. QED.
 */
double diversified_bi_loss(double n_machines, double daily_revenue, double recovery_days) {
    if (n_machines < 1.0 || daily_revenue < 0.0 || recovery_days < 0.0)
        return -1.0;
    return (1.0 / n_machines) * daily_revenue * recovery_days;
}

/*
 * concentration_premium — extra BI loss from concentration vs. diversification.
 *
 * premium = bi_loss(f) - bi_loss(1/n_equivalent)
 *
 * This is the additional BI exposure a mine carries by having one large machine
 * instead of n_equivalent smaller ones. An insurer charges more for this.
 *
 * f              — actual concentration fraction (0 < f <= 1.0)
 * n_equivalent   — number of machines in the diversified benchmark (>= 1)
 * daily_revenue  — total daily revenue (>= 0)
 * recovery_days  — days to restore (>= 0)
 *
 * Returns: concentrated_bi_loss(f) - diversified_bi_loss(n_equivalent) >= 0
 *          when f >= 1/n_equivalent (the concentrated machine handles more than one
 *          diversified machine would).
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 6: concentration_premium >= 0 when f >= 1/n_equivalent.
 *   Proof: premium = (f - 1/n)*rev*days. f >= 1/n and rev,days >= 0
 *   => (f - 1/n)*rev*days >= 0. QED.
 */
double concentration_premium(
    double f, double n_equivalent, double daily_revenue, double recovery_days
) {
    if (f <= 0.0 || f > 1.0 || n_equivalent < 1.0 ||
        daily_revenue < 0.0 || recovery_days < 0.0)
        return -1.0;
    double conc = concentrated_bi_loss(f, daily_revenue, recovery_days);
    double divr = diversified_bi_loss(n_equivalent, daily_revenue, recovery_days);
    if (conc < 0.0 || divr < 0.0)
        return -1.0;
    return conc - divr;
}

/*
 * diversification_ratio — fraction of max BI retained after diversification.
 *
 * ratio = bi_loss(n_machines) / bi_loss(1) = 1 / n_machines
 *
 * With 1 machine:  ratio = 1.0  (100% of max BI)
 * With 2 machines: ratio = 0.5  (50% of max BI)
 * With 4 machines: ratio = 0.25 (25% of max BI)
 *
 * Returns: 1/n_machines ∈ (0, 1] for n_machines >= 1.
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY: diversification_ratio ∈ (0, 1] for n_machines >= 1.
 *   Proof: 1/n_machines <= 1.0 (for n >= 1) and > 0 (for any finite n). QED.
 */
double diversification_ratio(double n_machines) {
    if (n_machines < 1.0)
        return -1.0;
    return 1.0 / n_machines;
}
