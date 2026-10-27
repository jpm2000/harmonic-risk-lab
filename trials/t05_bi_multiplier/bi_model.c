/*
 * bi_model.c — Business Interruption loss multiplier model.
 *
 * Source: Marsh "Mining Losses Uncovered" (2025).
 *
 * KEY FINDING: BI = ~80% of total gross losses in mining (2006-2025).
 * Patrick Walker (Rio Tinto): "A single grinding mill can process thousands
 * of tons of ore per day — a failure can trigger multi-month outages."
 *
 * THE MODEL:
 *   pd_loss       = direct property damage (equipment, structures)
 *   bi_loss       = daily_revenue × recovery_days
 *   total_loss    = pd_loss + bi_loss
 *   bi_ratio      = bi_loss / total_loss         (≈ 0.80 for mining average)
 *   bi_multiplier = total_loss / pd_loss         (≈ 5.0 at 80% BI share)
 *
 * VERIFIED PROPERTIES (see hypothesis.md):
 *   1. total_loss >= pd_loss
 *   2. bi_ratio ∈ [0, 1) when pd_loss > 0
 *   3. total_loss monotone in recovery_days
 *   4. bi_ratio monotone in recovery_days
 *   5. bi_loss >= 0
 *   6. bi_multiplier >= 1.0 when pd_loss > 0
 */

#include <math.h>

/*
 * bi_loss_amount — business interruption loss component.
 *
 * daily_revenue — revenue per operational day (>= 0, USD)
 * recovery_days — days to restore operations (>= 0)
 *
 * Returns: bi_loss = daily_revenue * recovery_days >= 0.
 * Returns: -1.0 for negative inputs.
 *
 * PROPERTY 5: bi_loss_amount >= 0 when daily_revenue >= 0, recovery_days >= 0.
 *
 * Note: Typical mining daily revenue ranges from $100K (small mine)
 *       to $10M+ (large open-pit copper or gold operation).
 *       At the $7B Brumadinho level, production value was ~$500K/day,
 *       with a multi-year recovery. BI loss dwarfed physical damage.
 */
double bi_loss_amount(double daily_revenue, double recovery_days) {
    if (daily_revenue < 0.0 || recovery_days < 0.0)
        return -1.0;
    return daily_revenue * recovery_days;
}

/*
 * total_insured_loss — sum of property damage and business interruption.
 *
 * pd_loss        — direct property damage loss (>= 0)
 * daily_revenue  — revenue per operational day (>= 0)
 * recovery_days  — days to restore operations (>= 0)
 *
 * Returns: total = pd_loss + bi_loss >= pd_loss.
 *
 * PROPERTY 1: total_insured_loss >= pd_loss for all valid inputs.
 *   Proof: total = pd + bi. bi >= 0 (property 5). Therefore total >= pd. QED.
 *
 * PROPERTY 3: total_insured_loss(pd, rev, d1) >= total_insured_loss(pd, rev, d2)
 *             when d1 >= d2 (monotone in recovery_days).
 *   Proof: total(d) = pd + rev*d. d1 >= d2 => rev*d1 >= rev*d2 (rev >= 0)
 *          => pd + rev*d1 >= pd + rev*d2. QED.
 */
double total_insured_loss(double pd_loss, double daily_revenue, double recovery_days) {
    if (pd_loss < 0.0 || daily_revenue < 0.0 || recovery_days < 0.0)
        return -1.0;
    double bi = bi_loss_amount(daily_revenue, recovery_days);
    return pd_loss + bi;
}

/*
 * bi_share — fraction of total loss attributable to business interruption.
 *
 * Marsh average: bi_share ≈ 0.80 for all mining claims.
 * For machinery breakdowns and structural failures: bi_share > 0.82.
 *
 * Returns: bi_ratio ∈ [0, 1) when pd_loss > 0.
 * Returns: 0.0 when pd_loss = 0 and recovery_days = 0 (no loss event).
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 2: bi_share ∈ [0, 1) when pd_loss > 0.
 *   Proof: bi_share = bi / (pd + bi).
 *   Numerator: bi >= 0.
 *   Denominator: pd + bi > pd > 0.
 *   So bi_share >= 0.
 *   bi_share < 1 iff bi < pd + bi iff 0 < pd. True by assumption. QED.
 *
 * PROPERTY 4: bi_share(pd, rev, d1) >= bi_share(pd, rev, d2) when d1 >= d2 and pd > 0.
 *   Proof: bi_share(d) = rev*d / (pd + rev*d).
 *   d/dx [rev*d / (pd + rev*d)] = pd*rev / (pd + rev*d)^2 > 0.
 *   So bi_share is strictly increasing in d when rev > 0. QED.
 */
double bi_share(double pd_loss, double daily_revenue, double recovery_days) {
    if (pd_loss < 0.0 || daily_revenue < 0.0 || recovery_days < 0.0)
        return -1.0;
    double bi  = bi_loss_amount(daily_revenue, recovery_days);
    double tot = total_insured_loss(pd_loss, daily_revenue, recovery_days);
    if (tot <= 0.0)
        return 0.0;
    return bi / tot;
}

/*
 * bi_multiplier — ratio of total insured loss to property damage alone.
 *
 * multiplier = total_loss / pd_loss = 1 + bi_loss / pd_loss
 *
 * When bi_share = 0.80: multiplier = 1 / (1 - 0.80) = 5.0
 * When recovery_days = 0: multiplier = 1.0 (no amplification)
 *
 * This is the core underwriting quantity: it tells an insurer how much
 * more than the physical damage they will need to pay.
 *
 * Returns: multiplier >= 1.0 when pd_loss > 0 and recovery_days >= 0.
 * Returns: -1.0 for invalid inputs.
 *
 * PROPERTY 6: bi_multiplier >= 1.0 when pd_loss > 0, daily_revenue >= 0,
 *             recovery_days >= 0.
 *   Proof: multiplier = (pd + bi) / pd = 1 + bi/pd. bi >= 0, pd > 0.
 *          So bi/pd >= 0, so multiplier >= 1.0. QED.
 */
double bi_multiplier(double pd_loss, double daily_revenue, double recovery_days) {
    if (pd_loss <= 0.0 || daily_revenue < 0.0 || recovery_days < 0.0)
        return -1.0;
    double tot = total_insured_loss(pd_loss, daily_revenue, recovery_days);
    return tot / pd_loss;
}
