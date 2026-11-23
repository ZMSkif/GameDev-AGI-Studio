---
name: web-monetization
description: Monetization and release strategy for HTML5 portal games - ad placement (interstitial, rewarded, banners), the in-app purchase catalog, telemetry, KPI thresholds, revenue scenarios, live-ops and storefront, with dated numbers and the owner's gates. Use for "how will this game earn", ad or IAP design, prices, which portal first, KPIs, sandbox metrics, covers or seasonal events. Not for purchase or save code (that is the platform adapter and the playgama-release skill).
---

# Web monetization

Binding: DEC-009 (#9), DEC-130 (#132) no spending or catalog change without the owner; DEC-110 (#112), DEC-111 (#113) estimates are never money received; DEC-107 (#109), DEC-108 (#110) LiveOps from real metrics, big changes with the owner; DEC-112 (#114) market intelligence; DEC-056 (#56) ads and payments behind adapters.

## The model to keep in mind

Revenue = traffic × play time × impressions × eCPM × share + purchases. Traffic depends on the cover's click rate and the platform's placement, which depend on metrics and updates. Play time multiplies impressions because the platform sets the interstitial interval. Ad slots and prices move revenue by percents; traffic and play time move it by multiples. So work in this order: the first minute and play time → retention → storefront → ads → purchases.

## Step 0: re-check live numbers

Shares, eCPM and rules change. With the Playgama MCP, read `get_game_checklist`, `get_game_guides` (monetization and first-session guides) and `get_bridge_sdk_docs`. Label every number: [O] official, [S] self-reported or second-hand, [C] calculated, [W] a working target the source set for itself. Anything older than 6 months is "re-check". Numbers below are from 17.11.2026.

## Ads

- **Interstitial:** at every natural pause (between levels, after a loss, leaving pause, shop or locker), never during play, never with own timers (platforms set 120–240 s [O]). Pause and mute through the platform events; that also enables the platform's "smart" ads.
- **Rewarded:** only on a button; the reward is visible before the ad; always declinable; granted only in the `rewarded` state; a bonus, never a condition of progress; a revive at most once per attempt. Good spots: double after a win; a second chance near the finish; double daily bonus; trying a skin; a hint after 30 s stuck. Target 3–5 watched per session, 30–40 % of offers taken [O].
- **Banners:** sticky or advanced only, one per screen, refresh no faster than 90 s, only on screens where players stay (menu, pause, results), safe area kept; add them only with an A/B test of retention.
- **Ad blockers** (≈ 30 % worldwide [S]): measure first (`checkAdBlock()` + an event and rewarded outcomes). Offer the coin alternative only after a real rewarded failure in this session; never punish by mistake.
- Equal-weight decline buttons next to ad offers; no ad offer in a slot the player just tapped; no confirmshaming.

## Purchases

- Show the shop only when `payments.isSupported`; prices only from `getCatalog()`.
- A casual catalog: "remove ads" (permanent; rewarded stays), 3–5 coin packs with rising value at $0.99–4.99 [O], a starter pack after the first session, cosmetics for coins.
- Forbidden: paid random rewards (loot boxes), real prizes, timer pressure on the first screen, fake "was" prices or popularity claims. Paying players are usually < 2 % [O]: purchases add to ads, they don't replace them.
- Economy check: the most expensive item ≈ 30–60 average sessions; a small pack ≈ 10 sessions of saved time.
- The exact catalog (ids, prices, consumable or not) is always the owner's call; changing it in the console is an owner-gated action (`playgama-release` skill).

## Telemetry before release

The platform already counts sessions, time, ads and purchases. Add 5–7 events with stable names and bounded values: `progression_started` / `_completed` / `_failed` with a step id; the key player decision (`<hook>_offer` with its outcome); `rewarded_offer_shown` with a placement; `shop_opened`, `iap_offer_shown`; `adblock_detected` once per session. No personal data, URLs or error texts. Under 30 measured sessions, say the conclusions are unreliable.

## KPIs and what to fix first

| KPI | Red | Yellow | Green |
|---|---|---|---|
| Click-to-play | < 55 % | 55–65 % | ≥ 65 % (Poki Web Fit [O]) |
| Play time per player per day | < 5 min | 5–10 | ≥ 10 (≥ 20 for CrazyGames) [W]; Poki asks ≥ 5 min [O] |
| Sessions under 60 s | > 40 % | 25–40 % | < 25 % [W] |
| D1 | < 18 % | 18–25 % | ≥ 25 % [W] (mobile median ≈ 22 % [S]) |
| D7 | < 3 % | 3–5 % | ≥ 5 % [W] (mobile median < 4 % [S]) |
| Rewarded watched per session | < 1 | 1–3 | 3–5 [O] |
| Rewarded taken / offered | < 15 % | 15–30 % | 30–40 % [O] |

Fix in the order click-to-play → play time → D1 → storefront → ads → purchases. Do not tune monetization while play time is red.

## Forecasts: scenarios only

Never promise income. Give three scenarios with inputs, formulas and monthly totals, labelled as estimates (DEC-111). Start from an honest base rate: on average cents per player over a game's life; hits are rare.

## Live-ops and storefront

- A small update every 2–4 weeks; seasonal events (New Year by ≈ 20.12 is the eCPM peak; expect a drop after 1 January).
- Cover = gameplay, one focus, the game's own style, never a generated collage (Playgama 4.3); two variants per slot; check it shrunk to tile size (≈ 170–200 px). Up to 3 words on the cover, not repeating the title.
- A 20–30 s video of real gameplay: 0–2 s result and stakes; 2–10 s one mechanic without menus; 10–20 s the twist; 20–30 s a loop point. 9:16 and 16:9; readable without sound.

## Platforms and platform risk

Choose the first portal by its sieve, not its audience size: Playgama and its network for games clear in 30 s; CrazyGames wants a unique twist, polish, 20+ minutes and English; Yandex wants Russian and ≥ 10 minutes of content; YouTube Playables wants under 30 MiB at start and long sessions, with no purchases. Poki requires a web exclusive, which blocks the other portals: always the owner's decision. Prove metrics on one platform, then widen with the same Bridge build and a per-platform storefront and QA. Keep a second exit ready.

## Ask the owner

Money, exclusives, traffic bonuses, prices, seasonal events and new ad formats are the owner's decisions. Ask in one batch, with options and the recommended one first (`orchestration-playbook` skill).

## Source

The monetization playbook and skill draft of the studio's first shipped web game (sources opened 17.11.2026) and the owner's monetization answers.
