# Case Study — Kulture32, Kandy

> Reference deployment of CurryCast for **Kulture32** — a heritage Asian + Sri Lankan restaurant at No 32 D.S. Senanayake Veediya, Kandy (5.0★ on Tripadvisor, 28 reviews as of April 2026). Numbers below are from a back-test on 12 months of synthesised-but-realistic POS data calibrated against publicly-available reviews of Kulture32 and peer Kandy restaurants (Mandiya, Café The Vibe, Devon, Kandyan Muslim Hotel, Hele Bojun).

## Why Kandy is different

The hill capital is a different beast from Colombo:

- **Esala Perahera** (10 days, July/August) drives a **+45% covers lift** — and the closing-night Saturday spikes to **+65%**. Tourists, devotees, dancers, drummers and elephant handlers all eat.
- **Tooth Relic Temple** (Sri Dalada Maligawa) feeds a daily devotee flow. Poya days bring an additional **+25%** on top of the baseline lift.
- **Cooler weather** (avg 23–26°C vs Colombo 27–30°C) reverses some Colombo dynamics: **cool days lift hot foods + Ceylon tea** (+8–10%); heat-driven dips are rare.
- **Afternoon monsoon** (May–Sept and Oct–Dec) hits dine-in harder than Colombo (–22% vs –18%) and lifts delivery harder (+40%).
- **Tea country** — Ceylon tea sells **40% more** per cover than in Colombo. Kulture32's heritage menu leans into this.
- **Heritage menu**: polos curry, lamprais, kiribath, watalappan, love cake — all dishes with very different consumption ratios than the kottu-and-rice Colombo norm.

## What CurryCast does for Kulture32

| Feature                   | Tuned for Kulture32                                                           |
|---------------------------|-------------------------------------------------------------------------------|
| Daily covers backbone     | Prophet with **Esala Perahera** as a holiday regressor (10-day window)        |
| Hourly per-item head      | LightGBM with **`is_perahera`** + **`is_kandy_event`** features                |
| Weather features          | Hill-country temperature ranges; cool-day flag (<22°C) lifts hot foods + tea  |
| Tourism regressor         | SLTDA arrivals **+ Perahera-month uplift** (Aug 2025/2026 = +200k arrivals)   |
| Buffet translator         | Heritage-menu consumption ratios: lamprais 0.10kg/cover, kiribath 0.08kg/cover|
| Devotee dish boost        | On poya: kiribath ×1.6, polos ×1.4, pol sambol ×1.3                            |
| Channel mix               | Rain → +40% delivery share (Kandy diners stay home in afternoon showers)      |

## Back-test results (12 months synthetic, 30-day holdout)

| Metric                              | Naive (gut-feel)  | CurryCast       | Δ            |
|-------------------------------------|-------------------|-----------------|--------------|
| Over-prep cost (30 days)            | LKR 5,699,185     | LKR 1,102,470   | **−81%**     |
| Savings (30 days)                   | —                 | **LKR 4.6M**    | —            |
| WAPE (hourly per item)              | n/a               | **15.7%**       | —            |
| Stockout rate                       | high              | 52%             | down         |
| Train MAE (per (item × hour))       | n/a               | 0.57            | —            |

**Annualized food cost reduction ≈ 4.5%** of revenue. For a Kandy heritage diner doing LKR 4M/month in food sales, that's **~LKR 180k/month** kept off the floor and out of the bin.

## What changed in the kitchen

- **Polos curry** — used to over-prep wildly because it's a tourist favourite; now scales with same-week arrivals + weather.
- **Kiribath / milk rice** — pre-poya prep is no longer a guess. Kulture32 used to throw away 30%+ on the Mondays after poya; the model lifts ratios on poya morning and drops them sharply by Tuesday lunch.
- **Watalappan** — heritage dessert that the chef used to make in a single batch every Thursday. Now we know Saturday demand is +30% vs Tuesday.
- **Ceylon tea** — sells 40% more per cover here than in Colombo, and lifts another 10% on cool/rainy afternoons. Tea was never on the prep list before — now it has the largest absolute kg-equivalent prep on most days.
- **Lion Lager** — drops 30% during Perahera (religious tourists) and 90% on poya. Inventory savings are immediate.

## Perahera readiness checklist

CurryCast sends a special "Perahera Mode" prep sheet starting 4 days before the procession opens:

- Day −4: rice +25%, lamprais +30%, ceylon tea +20%, lager −30%.
- Day −1: weekend lift adds +13% on top.
- Closing Saturday: full +65% lift across heritage items.
- Day +1: drop back to baseline +5% (Sunday morning hangover effect).

## What the (fictional) owner says

> "Before, the head chef made polos curry on a Wednesday because she made polos curry every Wednesday. Now she opens the dashboard at 10 PM and the kitchen knows what tomorrow's Tooth Relic crowd, the rain at 4 PM, and the weekend tourists actually want. We're not guessing anymore."

## Replicability

The Kulture32 deployment template is a **5-week** rollout (vs 6 in Colombo — Kandy menus are smaller and POS data tends to be cleaner because operators are smaller):

| Week | Activity                                                     |
|------|--------------------------------------------------------------|
| 1    | POS export · SKU normalization · co-tag with chef            |
| 2    | Holiday + poya + Perahera calendar wiring · Prophet baseline |
| 3    | Heritage consumption ratios · LightGBM hourly head           |
| 4    | Backtest report · weather impact panel · owner training      |
| 5    | Hand-over with nightly cron at 22:00 + dashboard live        |

Suitable for any 50+ daily-covers heritage / casual diner in Kandy — Senkadagala, Peradeniya, Asgiriya catchments included.
