# Norunja (노른자) — Word-of-Mouth Simulator for First-Time Café Founders

**Team 5, AI Universities Joint Hackathon (sponsored by Syntitan)**

Before you open a café, let the neighborhood talk about it first.

Norunja spreads the news of a not-yet-opened café through **30,000 virtual citizens across Seoul's 426 administrative neighborhoods (dong)** and shows, week by week for 12 weeks, who hears about it, who passes it on, who actually visits, and when the shop breaks even. Founders can change the concept, target customers, location, opening hours, price, costs, and promotion budget, re-run, and compare.

- **Live demo:** https://norunja.streamlit.app
- **Repository:** https://github.com/user24345/5
- **Demo video:** [link]

---

## Why

Large franchises analyze commercial-district data every time they open a new store. Individual founders mostly rely on legwork and gut feeling. Existing district-analysis services show neighborhood *averages* (foot traffic, sales), but not how a specific concept spreads through word of mouth, or how results change when you change the concept, hours, price, or promotion.

Our synthetic surveys showed how much these choices interact. For a kids-friendly brunch café, 92% of housewives in their 30s said they could pay ₩10,000 or more, but only 55% of those in their 40s did. In our simulation of a commuter take-out coffee shop in Yeoksam 1-dong, spending a ₩1M budget entirely on Instagram ads added 13 customers over 12 weeks, while an opening discount (about ₩480K in discounts) added 382.

## What it does

| Feature | What the founder gets |
| --- | --- |
| **Word-of-mouth map** | A week-by-week map of who heard about the shop, and neighborhoods ranked by the founder's *target* customers |
| **"What should I change?"** | Rule-based checks on price, opening hours, and location type, plus an AI-written diagnosis and revised business idea |
| **Promotion plan** | Budget split across Danggeun (local marketplace) ads, Instagram, mom-community banners, blogger reviews, and opening discounts, with extra customers and the week the ad spend pays back |
| **12-week action plan** | When, what, for whom, and how much — including which community to ask for first reviews (e.g. Instagram for people in their 20s, mom cafés for housewives in their 30s, neighbor referrals for people 50+) |
| **Hours what-if** | When the app suggests longer hours, it re-runs the engine with those hours and shows the change in customers |
| **After-open calibration** | Enter real customer counts for weeks 1–4 and the forecast, break-even week, and re-promotion timing are re-fitted |

## How it works

```
Inputs (shop description, up to 3 neighborhoods, optional: location pin, hours, days, rent, price, fixed costs, budget)
   │
   ├─ Detect target customers and shop type from the description
   ├─ Pick the matching Syntitan survey (base + 5 shop types), normalized to the base survey's Seoul average
   │
   ▼
Diffusion engine (Python, agent-based)
   12 weeks × 2 steps/week, 3 km radius, 5 random seeds averaged
   neighbor and community (Danggeun, Instagram, mom cafés, campus community) spread,
   search after reviews accumulate, walk-in discovery, distance, competition, hours and day-of-week effects,
   promotion scenarios and greedy budget allocation, break-even
   │
   ▼
Rule-based judgments (price burden, hours fit, location type, target group, first-review community)
   │
   ▼
LLM diagnosis (gpt-4.1-mini) — writes only from pre-computed facts; rule-violating sentences are filtered out
   │
   ▼
Streamlit app (map, comparison, fix cards, plan, promotion, channels, word-of-mouth, after-open calibration)
```

**Design principle:** numbers are computed by the engine, judgments are made by code, and the LLM only explains. In early tests the LLM miscounted, converted units incorrectly (₩2M became ₩20M), and treated hypothetical survey answers as facts, so we narrowed its role.

## Data

| Data | Source | Used for |
| --- | --- | --- |
| ~30,000 virtual citizens in 15 age × occupation groups across 426 dong | Built from [NVIDIA Nemotron-Personas-Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea) (CC BY 4.0) | Agents in the simulation |
| Foot traffic, worker population, time/age/weekday shares, store counts, rent, café sales and transactions by dong | Seoul Commercial District Analysis Service, 2025 | Daytime seeds, competition, hours effects, location type, validation |
| Group-level reactions to a café (9 questions) | Syntitan synthetic surveys, 6 types; Seoul respondents (~1,600 per survey) filtered from 8,561 nationwide | Interest, sharing and revisit intent, discovery channels, willingness to pay, visit times, promotion response |
| Ad unit costs | Team research (Danggeun ₩300/click, Instagram ₩18K per 1,000 impressions, blogger review ₩100K/person, mom-café banner ₩200K/month) | Promotion costs |
| Real shop cases | News articles, Korea Small Business Agency, platform case books | Channel playbooks |
| Map | © OpenStreetMap contributors | Result map, location pin |

### How we used Syntitan

The engine decides who hears the news; Syntitan tells us how each group *reacts* to it. We used the same 9-question survey in three stages:

1. **Base survey** ("a reasonably priced dessert café for university students in their 20s") to calibrate customer counts against real card transactions and to validate against real café sales.
2. **Re-survey of AI-revised ideas** for Seogyo, Yeonnam, and Mangwon 1-dong. Interest from people in their 20s held, but interest from people 30+ dropped by 0.5–1.4 points, which could weaken neighborhood word of mouth. This is why the LLM explains results instead of making decisions.
3. **Five shop-type surveys** (commuter coffee, kids brunch, senior café, photo-worthy dessert café, low-price student drinks), adding a "weekday morning" visit time.

Shop-type surveys differ in overall friendliness, so we shift each one so its Seoul-wide average (interest, sharing, revisit) matches the base survey before feeding it to the engine. Differences *between groups* are kept.

## Validation

Each check had a metric and a pass threshold set in advance.

| Check | Result | Verdict |
| --- | --- | --- |
| Engine property tests | 16/16 | Pass |
| Neighborhood demand (before competition) vs. real 2025 café sales rank, 410 dong | Spearman +0.25 (95% CI ≈ 0.16–0.34, p < 0.001) | Pass (weak positive) |
| New-shop customers (after competition) vs. real café sales rank | −0.01 (p = 0.85) | Not yet |
| Baselines on the same dong | store count +0.87, workers +0.66, foot traffic +0.42 | Simple indicators predict district-level sales better |
| Discovery channels vs. survey | Mean absolute error 6.5 pp (walk-ins under-estimated by 12.1 pp) | Pass |
| After-open calibration (4 weeks observed, 8 forecast) | Error reduced 32–51%, improved in 72–82% of 50 trials | Pass |
| AI diagnosis numbers vs. result tables | 1,379 of 1,389 numbers match (99.3%) across 35 diagnoses | Pass |
| Bug checklist | 7/9 → 9/9 after fixes | Pass |

**How to read this:** Norunja is a tool for *comparing* concepts, neighborhoods, and conditions, not for predicting exact revenue. Using café store count as demand (not only as competition) is our first improvement target.

## Getting started

```bash
git clone https://github.com/user24345/5.git
cd 5
pip install -r requirements.txt

# optional: enables the AI diagnosis (the app still works without it)
export OPENAI_API_KEY="sk-..."          # PowerShell: $env:OPENAI_API_KEY = "sk-..."

streamlit run app_v3.py
```

On Streamlit Community Cloud, put the key in **Settings → Secrets**:

```toml
OPENAI_API_KEY = "sk-..."
```

### Engine commands

```bash
python engine/simulate.py                                          # demo neighborhoods
python engine/simulate.py --all-dongs --out outputs/validation_run  # all 426 dong
python engine/simulate.py --no-promo                               # without promotion scenarios
python engine/calibrate.py                                         # fit customer scale to real transactions
python engine/open_calibrate.py --demo                             # after-open calibration demo
python tests/test_engine.py                                        # 16 engine property tests
```

## Repository layout

```
app_v3.py                      Streamlit entry point (inputs, engine runs, rules, AI diagnosis)
frontend/v3/view.html          Result page template
frontend/data/real/            Data the app reads
  personas.csv                 Virtual citizens
  dong_stats.csv               Seoul district statistics by dong
  dongs.geojson                Dong boundaries
  reactions.json               Base Syntitan survey (by group)
  reactions_types/             Shop-type surveys (commute, kids, senior, photo, teen)
  ad_costs.json                Ad unit costs
engine/
  simulate.py                  Diffusion and visit simulation
  promo.py                     Promotion scenarios and budget allocation
  calibrate.py                 Customer-scale calibration
  open_calibrate.py            After-open calibration
  compare_revision.py          Before/after comparison for AI-revised ideas
config/weights.json            Model assumptions
tests/test_engine.py           Engine property tests
diagnose_business_2.py         AI diagnosis prompt and helpers
```

## Limitations

- No interviews or usability tests with real founders yet; validation uses public data and internal scenario tests.
- Surveys exist for 6 shop types; other concepts use the closest one. Synthetic answers may be friendlier than real ones.
- Agents are residents only, so visitor-heavy districts (e.g. Yeonnam-dong) and tourist-oriented shops score low.
- The oldest group is "50+", so people in their 60s and 70s are not separated; teen and college students share one group (survey answers are split by age, customer counts are not).
- Foot-traffic data ends at midnight; late-night demand is not modeled.
- Price elasticity is not modeled; price advice is directional.
- Ads are assumed to reach the whole neighborhood evenly.
- Thresholds such as age-based price ceilings, concept multipliers, location cut-offs, 60% margin, and ₩5M default fixed costs are team assumptions.

## Roadmap

- Use café store count and worker population as demand signals
- Grow the survey library; survey new concepts in the background and reuse them
- Add visitors and commuter flows; split ages 60+ and teens
- Channel effects weighted by the target group's actual channel use
- Concrete promotion coaching (post copy, photo ideas, weekly to-dos) that updates after opening
- Other industries (restaurants, academies, salons, fitness, retail) and other cities
- Pilot tests with real founders

## Team

| Name | Role |
| --- | --- |
| Seungyeon Cha (Sogang Univ.) | PM, diffusion engine, promotion simulation, app |
| Junhyuk Song (Korea Univ.) | Syntitan surveys, AI diagnosis, ad costs |
| Jieun Byun (Ewha Womans Univ.) | Virtual citizens, district data, validation |
| Junan Jung (Seoul National Univ. of Science and Technology) | UI review, deployment, case research |

## Acknowledgments

- Synthetic survey data: **Syntitan**
- District data: Seoul Commercial District Analysis Service
- Map data: © OpenStreetMap contributors
- Persona data: [NVIDIA Nemotron-Personas-Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea), licensed under CC BY 4.0
