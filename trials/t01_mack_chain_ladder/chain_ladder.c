/*
 * chain_ladder.c — Mack Chain Ladder for IBNR reserve estimation.
 *
 * Source: Mack (1993). "Distribution-free calculation of the standard error
 * of chain ladder estimates." ASTIN Bulletin 23(2): 213–225.
 *
 * Also formalized in Lean 4: github.com/Robby955/verified-reserving
 *
 * This file contains the core computational functions.
 * For the full development triangle processing, see run_trial.py.
 */

#include <math.h>
#include <stddef.h>

/*
 * development_factor — Link ratio between two consecutive development periods.
 *
 * In the chain ladder, the development factor f_k represents how much
 * cumulative paid claims grow from development period k to k+1.
 *
 * paid_t  — cumulative paid claims at period t   (must be > 0)
 * paid_t1 — cumulative paid claims at period t+1 (must be > 0)
 *
 * Returns: f = paid_t1 / paid_t  (always > 0 when inputs are valid)
 * Returns: -1.0 for invalid inputs (non-positive paid amounts)
 *
 * PROPERTY 1: development_factor > 0 for all paid_t > 0, paid_t1 > 0.
 */
double development_factor(double paid_t, double paid_t1) {
    if (paid_t <= 0.0 || paid_t1 <= 0.0)
        return -1.0;
    return paid_t1 / paid_t;
}

/*
 * weighted_factor — Volume-weighted average development factor across accident years.
 *
 * This is the standard chain ladder weighting:
 *   f_k = sum(C_{i,k+1}) / sum(C_{i,k})
 *
 * numerator   — sum of paid claims in the later period    (must be > 0)
 * denominator — sum of paid claims in the earlier period  (must be > 0)
 *
 * Returns: f = numerator / denominator
 * Returns: -1.0 for invalid inputs
 *
 * PROPERTY: weighted_factor(a, b) = development_factor(b, a) in structure.
 *           Result > 0 when inputs > 0.
 */
double weighted_factor(double numerator, double denominator) {
    if (numerator <= 0.0 || denominator <= 0.0)
        return -1.0;
    return numerator / denominator;
}

/*
 * predict_ultimate — Project ultimate losses by applying tail factors.
 *
 * current_paid — most recent cumulative paid amount for an accident year (> 0)
 * tail_factor  — product of all remaining development factors (>= 1.0 means
 *                losses only develop upward, which is the standard assumption)
 *
 * Returns: ultimate = current_paid * tail_factor
 * Returns: -1.0 for invalid inputs
 *
 * PROPERTY 2: predict_ultimate >= current_paid when tail_factor >= 1.0 and
 *             current_paid > 0.
 */
double predict_ultimate(double current_paid, double tail_factor) {
    if (current_paid <= 0.0 || tail_factor <= 0.0)
        return -1.0;
    return current_paid * tail_factor;
}

/*
 * ibnr_reserve — Incurred But Not Reported reserve for one accident year.
 *
 * ultimate     — estimated total ultimate losses (>= current_paid)
 * current_paid — losses paid to date             (>= 0)
 *
 * Returns: IBNR = ultimate - current_paid   (always >= 0 for valid inputs)
 * Returns: -1.0 if ultimate < current_paid or any input is negative
 *
 * PROPERTY 3: ibnr_reserve >= 0 when ultimate >= current_paid >= 0.
 * PROPERTY 4: ibnr_reserve returns -1.0 when ultimate < current_paid.
 */
double ibnr_reserve(double ultimate, double current_paid) {
    if (current_paid < 0.0 || ultimate < 0.0 || ultimate < current_paid)
        return -1.0;
    return ultimate - current_paid;
}

/*
 * total_ibnr — Sum of IBNR across all accident years.
 *
 * reserves   — array of per-accident-year IBNR values
 * n          — number of accident years (>= 1)
 *
 * Returns: sum of all non-negative reserves.
 *          If any element < 0 (sentinel), returns -1.0.
 *
 * PROPERTY 5: total_ibnr >= 0 when all reserves[i] >= 0.
 */
double total_ibnr(const double *reserves, int n) {
    if (n < 1 || reserves == NULL)
        return -1.0;
    double total = 0.0;
    for (int i = 0; i < n; i++) {
        if (reserves[i] < 0.0)
            return -1.0;  /* propagate sentinel */
        total += reserves[i];
    }
    return total;
}
