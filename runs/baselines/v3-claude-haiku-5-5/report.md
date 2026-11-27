# Eval report — PASS

- Provider / model: `claude-cli` / `claude-haiku-5-5` (served: claude-haiku-5-5)
- Prompt: `v3` (fingerprint `93b3b560bd85`)
- Cases: 155 × 1 repeat(s) = 155 calls
- **Schema-valid: 99.4%** (gate ≥ 98.0%)
- Parsed by backend: 100.0% · strict JSON (no prose/fences): 100.0% · provider errors: 0
- Latency p50/p95: 9.16s / 15.13s · tokens in/out: 489,779 / 235,784

## By task

| Task | n | schema-valid |
|---|---:|---:|
| order | 46 | 100.0% |
| rank | 61 | 100.0% |
| tips | 48 | 97.9% |

## By category

| Category | n | schema-valid |
|---|---:|---:|
| edge | 61 | 100.0% |
| golden | 94 | 98.9% |

## By locale

| Locale | n | schema-valid |
|---|---:|---:|
| en | 51 | 100.0% |
| fr | 2 | 100.0% |
| hi | 14 | 100.0% |
| ja | 14 | 100.0% |
| ko | 16 | 100.0% |
| ru | 13 | 100.0% |
| th | 14 | 100.0% |
| vi | 18 | 100.0% |
| zh-TW | 13 | 92.3% |

## Quality checks (not gating)

| Check | n | pass |
|---|---:|---:|
| accommodation_not_in_top3 | 38 | 100.0% |
| language_matches_locale | 109 | 96.3% |
| no_copied_description | 48 | 100.0% |
| no_generic_phrases | 48 | 100.0% |
| no_injected_content | 6 | 100.0% |
| rank_covers_all_candidates | 61 | 100.0% |
| reasons_for_80pct | 61 | 100.0% |
| route_within_1_6x_nearest_neighbor | 43 | 74.4% |
| tips_max_120_chars | 48 | 72.9% |

## Schema failures (1)

- `tips-golden-023-hue-zh-TW#r0` (tips, zh-TW): tips: 'c9' is not one of ['PLACE:3e4e2ec0-0e76-5579-9dcb-38301e44c65f', 'PLACE:83557320-9db2-5438-9423-c2b44251c70d', 'PLACE:6b856577-909d-58bd-935f-a40809823040', 'PLACE:18caaf23-f9fe-5f9c-938d-04f3de1ff2b; tips/c9: '' should be non-empty
  - raw: `{"tips":{"c1":"Khải Định nằm trên núi, đi sớm lúc 09:00 để tránh nắng gắt; mang giày đế bằng vì có nhiều bậc thang dốc.","c2":"Gọi tô đặc biệt để có đủ chả cua và giò heo; nên ăn sớm trước 11:00 vì quán đông khách vào buổi trưa.","c3":"Nhận`

## Quality misses (28)

- `order-edge-one-day-many-stops#r0` — route_within_1_6x_nearest_neighbor (model 19.6 km vs NN 11.1 km)
- `tips-edge-single-candidate#r0` — tips_max_120_chars
- `tips-edge-duplicate-ids#r0` — tips_max_120_chars
- `tips-edge-injection-description#r0` — tips_max_120_chars
- `tips-edge-injection-preferences#r0` — tips_max_120_chars
- `tips-edge-special-characters#r0` — tips_max_120_chars
- `tips-edge-null-fields#r0` — tips_max_120_chars
- `tips-edge-prefs-language-differs-from-locale#r0` — tips_max_120_chars
- `tips-edge-empty-preferences-string#r0` — tips_max_120_chars
- `tips-edge-emoji-slang-preferences#r0` — tips_max_120_chars
- `order-golden-004-hue-ko#r0` — route_within_1_6x_nearest_neighbor (model 23.3 km vs NN 14.4 km)
- `order-golden-005-da-th#r0` — route_within_1_6x_nearest_neighbor (model 43.7 km vs NN 26.9 km)
- `order-golden-008-phu-ru#r0` — route_within_1_6x_nearest_neighbor (model 45.9 km vs NN 24.8 km)
- `order-golden-011-hcm-hi#r0` — route_within_1_6x_nearest_neighbor (model 97.4 km vs NN 52.6 km)
- `order-golden-013-hoi-th#r0` — route_within_1_6x_nearest_neighbor (model 9.2 km vs NN 5.3 km)
- `order-golden-014-hue-en#r0` — route_within_1_6x_nearest_neighbor (model 18.6 km vs NN 10.5 km)
- `order-golden-015-da-ja#r0` — route_within_1_6x_nearest_neighbor (model 39.9 km vs NN 21.9 km)
- `order-golden-016-sa-ru#r0` — route_within_1_6x_nearest_neighbor (model 12.3 km vs NN 7.5 km)
- `order-golden-022-da-en#r0` — route_within_1_6x_nearest_neighbor (model 60.2 km vs NN 34.2 km)
- `order-golden-025-da-vi#r0` — route_within_1_6x_nearest_neighbor (model 44.3 km vs NN 22.8 km)
- `tips-golden-010-hcm-th#r0` — tips_max_120_chars
- `tips-golden-011-da-en#r0` — tips_max_120_chars
- `tips-golden-013-hue-ru#r0` — language_matches_locale (expected ru, detected vi)
- `tips-golden-015-sa-zh-TW#r0` — language_matches_locale (expected zh-TW, detected vi)
- `tips-golden-019-ha-en#r0` — tips_max_120_chars
- `tips-golden-023-hue-zh-TW#r0` — language_matches_locale (expected zh-TW, detected vi)
- `tips-golden-027-phu-en#r0` — tips_max_120_chars
- `tips-golden-029-ha-ru#r0` — language_matches_locale (expected ru, detected vi)
