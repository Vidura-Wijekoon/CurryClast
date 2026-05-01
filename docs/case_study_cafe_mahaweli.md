# Case Study — Café Mahaweli

> *Anonymized reference deployment. Café Mahaweli is a fictional composite of mid-size Colombo casual diners with a lunch buffet.*

## The pain

Café Mahaweli serves rice & curry buffet at lunch and switches to à la carte (kottu, devilled chicken, hoppers) at dinner. Average daily covers: ~120, swinging between 60 and 220.

Before CurryCast, the head chef ordered ingredients on **Tuesday for the whole week** based on the prior week's sales. The result:

- Saturdays during tourist season: ran out of pol sambol by 8 PM.
- Mondays after a poya: prepped 200 kg of rice, served 110 kg, threw out the rest.
- Rainy Thursday: kottu sat in the chafer until 10 PM and went home with staff.

Owner-estimated waste: **18% of food cost**.

## The deployment (4 weeks)

| Week | Activity                                                       |
|------|----------------------------------------------------------------|
| 1    | POS export (NooDelo CSV); SKU normalization                    |
| 2    | Weather + holiday + tourism feature joins; Prophet baseline    |
| 3    | LightGBM hourly head; back-test report on prior 30 days        |
| 4    | Owner training; nightly cron at 22:00; Streamlit dashboard live|

Total integration effort: ~120 engineering hours.

## The numbers (back-test on 12 months)

| Metric                       | Before    | After     | Δ           |
|------------------------------|-----------|-----------|-------------|
| Food cost (% of revenue)     | 34%       | 30%       | **−4 pp**   |
| Monthly waste (LKR)          | 760,000   | 480,000   | **−280k**   |
| Stockout incidents (per mo.) | 16        | 6         | **−62%**    |
| Pol sambol over-prep (kg/wk) | 22 kg     | 6 kg      | **−72%**    |
| WAPE — daily covers          | n/a       | 11.4%     | —           |
| WAPE — hourly per item       | n/a       | 18.7%     | —           |

**Annualized savings: ~LKR 3.4 million** on LKR 72 million revenue.

## What changed in the kitchen

- Rice prep moved from 22 kg (gut-feel) to a CurryCast-suggested daily kg. Day-of-week swing now reflects expected covers, not what happened last Tuesday.
- Kottu portions for rainy Fridays auto-bumped 12% (comfort food). Drinks downshifted.
- Lion Lager order on poya days dropped 90%. The chef noticed within two weeks.
- Tourist season weekend prep now scales with SLTDA arrival data — not with the chef's mental model from last December.

## What the owner says

> "We're still cooking, but we're not guessing anymore. The Saturday queue is steady because we don't run out, and Monday lunch break-even is lower because we don't over-prep."

## Replicability

The Café Mahaweli approach is a templated 6-week deployment:
1. Pull POS export.
2. Normalize SKUs (RapidFuzz + 30-min review with the chef).
3. Train + back-test.
4. Deploy nightly cron + dashboard.
5. Two weeks of co-management with chef.
6. Hand over.

Suitable for any 60+ daily-covers restaurant in Sri Lanka.
