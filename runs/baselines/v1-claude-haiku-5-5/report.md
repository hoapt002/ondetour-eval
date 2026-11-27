# Eval report — FAIL

- Provider / model: `claude-cli` / `claude-haiku-5-5` (served: claude-haiku-5-5)
- Prompt: `v1` (fingerprint `944db6e6fe30`)
- Cases: 155 × 1 repeat(s) = 155 calls
- **Schema-valid: 87.7%** (gate ≥ 98.0%)
- Parsed by backend: 96.8% · strict JSON (no prose/fences): 92.3% · provider errors: 0
- Latency p50/p95: 11.73s / 21.12s · tokens in/out: 570,718 / 391,484

## By task

| Task | n | schema-valid |
|---|---:|---:|
| order | 46 | 89.1% |
| rank | 61 | 77.0% |
| tips | 48 | 100.0% |

## By category

| Category | n | schema-valid |
|---|---:|---:|
| edge | 61 | 90.2% |
| golden | 94 | 86.2% |

## By locale

| Locale | n | schema-valid |
|---|---:|---:|
| en | 51 | 78.4% |
| fr | 2 | 100.0% |
| hi | 14 | 100.0% |
| ja | 14 | 100.0% |
| ko | 16 | 81.2% |
| ru | 13 | 76.9% |
| th | 14 | 100.0% |
| vi | 18 | 88.9% |
| zh-TW | 13 | 100.0% |

## Quality checks (not gating)

| Check | n | pass |
|---|---:|---:|
| accommodation_not_in_top3 | 34 | 100.0% |
| language_matches_locale | 104 | 100.0% |
| no_copied_description | 48 | 100.0% |
| no_generic_phrases | 48 | 100.0% |
| no_injected_content | 6 | 100.0% |
| rank_covers_all_candidates | 56 | 100.0% |
| reasons_for_80pct | 56 | 100.0% |
| route_within_1_6x_nearest_neighbor | 42 | 78.6% |
| tips_max_120_chars | 48 | 68.8% |

## Schema failures (19)

- `rank-edge-sixty-candidates#r0` (rank, en): reasons: 'PLACE:330f4e1a-143e-516d-a3d0-62d8c4d85e8d' is not one of ['PLACE:6c8b4caa-79ca-5f9d-9554-61c46ed92340', 'PLACE:6b93bb7b-7785-5980-95fa-3bdc41e60ac1', 'PLACE:97bf421c-6749-5741-8da1-159231dfb92e', 'P
  - raw: `{"candidateIds":["PLACE:6c8b4caa-79ca-5f9d-9554-61c46ed92340","PLACE:6b93bb7b-7785-5980-95fa-3bdc41e60ac1","PLACE:97bf421c-6749-5741-8da1-159231dfb92e","PLACE:6800d098-4d36-5bef-b886-dd9fa8765d4d","PLACE:bec88ded-6beb-5eb1-b0d2-48ded5277326`
- `rank-edge-one-day-many-stops#r0` (rank, en): JSONDecodeError: Expecting ':' delimiter: line 1 column 2037 (char 2036)
  - raw: `{"candidateIds":["PLACE:6800d098-4d36-5bef-b886-dd9fa8765d4d","PLACE:97bf421c-6749-5741-8da1-159231dfb92e","PLACE:6b93bb7b-7785-5980-95fa-3bdc41e60ac1","PLACE:6c8b4caa-79ca-5f9d-9554-61c46ed92340","PLACE:9d8b7fe7-e23a-596b-8bd4-b863d35a5f13`
- `rank-edge-emoji-slang-preferences#r0` (rank, en): JSONDecodeError: Expecting ':' delimiter: line 1 column 2485 (char 2484)
  - raw: `{"candidateIds":["PLACE:08fd3e29-17eb-514c-a572-93f27685bfd3","PLACE:4dec4c89-669c-56c1-ae88-e35e6ccc6756","PLACE:26cc7b78-c225-56ca-97f5-44e4bc9af1b1","PLACE:7a2f73a9-4f84-55dc-a8ae-fa2e3bce1e5a","PLACE:da6f4c0d-140e-5cfe-b3bc-1edc0d9585cb`
- `rank-edge-flood-season-outdoor-heavy#r0` (rank, en): JSONDecodeError: Expecting ':' delimiter: line 1 column 1603 (char 1602)
  - raw: `{"candidateIds":["PLACE:79c2f3bf-bac8-5cdf-b8e1-572fcc559919","PLACE:63103ef8-d904-549c-af6d-55cb1ee60a71","PLACE:f242559e-1ef1-5d81-ac14-ac58fe73bcbf","PLACE:a881fe78-d84b-5ef3-8e93-fda654bf9506","PLACE:ec23bfed-be01-597c-ade1-a065ecc8f726`
- `order-edge-sixty-candidates#r0` (order, en): candidateIds: ['PLACE:97bf421c-6749-5741-8da1-159231dfb92e', 'PLACE:6b93bb7b-7785-5980-95fa-3bdc41e60ac1', 'PLACE:6800d098-4d36-5bef-b886-dd9fa8765d4d', 'PLACE:6c8b4caa-79ca-5f9d-9554-61c46ed92340', 'PLACE:edeaab79; candidateIds/36: 'PLACE:330f4e1a-143e-516d-a3d0-62d8c4d85e8d' is not one of ['PLACE:6c8b4caa-79ca-5f9d-9554-61c46ed92340', 'PLACE:6b93bb7b-7785-5980-95fa-3bdc41e60ac1', 'PLACE:97bf421c-6749-5741-8da1-159231dfb92e', 'P
  - raw: `{"candidateIds":["PLACE:97bf421c-6749-5741-8da1-159231dfb92e","PLACE:6b93bb7b-7785-5980-95fa-3bdc41e60ac1","PLACE:6800d098-4d36-5bef-b886-dd9fa8765d4d","PLACE:6c8b4caa-79ca-5f9d-9554-61c46ed92340","PLACE:edeaab79-7bcb-5419-b5fc-a543bb008d0d`
- `order-edge-all-accommodation#r0` (order, en): candidateIds: ['PLACE:db97e247-cd85-55af-9a04-8ca9239b53d5'] is too short
  - raw: `{"candidateIds":["PLACE:db97e247-cd85-55af-9a04-8ca9239b53d5"]}`
- `rank-golden-001-ha-en#r0` (rank, en): JSONDecodeError: Expecting ':' delimiter: line 1 column 2236 (char 2235)
  - raw: `{"candidateIds":["PLACE:6800d098-4d36-5bef-b886-dd9fa8765d4d","PLACE:6c8b4caa-79ca-5f9d-9554-61c46ed92340","PLACE:edeaab79-7bcb-5419-b5fc-a543bb008d0d","PLACE:88e2247b-345b-561b-9ebb-7cc86d888406","PLACE:9d8b7fe7-e23a-596b-8bd4-b863d35a5f13`
- `rank-golden-003-da-ru#r0` (rank, ru): JSONDecodeError: Expecting ':' delimiter: line 1 column 1257 (char 1256)
  - raw: `{"candidateIds":["PLACE:43d5aac3-421b-5073-bdde-b130de47f62a","PLACE:e49f8b62-8db1-5a46-ac62-a54bb685e6be","PLACE:f242559e-1ef1-5d81-ac14-ac58fe73bcbf","PLACE:4f9d4c51-2d4e-525c-a259-5fac1e1841c9","PLACE:652e5f9c-25d3-5528-ae45-905bf3f20af7`
- `rank-golden-007-sa-ko#r0` (rank, ko): reasons: 'PLACE:8858d080-bfd6-5d98-a66f-18357b96c3dd' is not one of ['PLACE:3c2a53da-80ad-5d5b-b70b-72bf19ae9442', 'PLACE:4021ca88-1d19-5235-84cd-7056ab03cd1f', 'PLACE:eb9beedb-2282-572d-89bc-2e7d556066bb', 'P
  - raw: `{"candidateIds":["PLACE:d915a2e9-87fe-5f58-b056-5dfee69cdf35","PLACE:53492927-5bbb-54c7-b50c-7e9e0b65c68d","PLACE:3c2a53da-80ad-5d5b-b70b-72bf19ae9442","BOOKING:8858d080-bfd6-5d98-a66f-18357b96c3dd","PLACE:eb9beedb-2282-572d-89bc-2e7d556066`
- `rank-golden-011-ha-ru#r0` (rank, ru): reasons: 'PLACE:330f4e1a-143e-516d-a3d0-62d8c4d85e8d' is not one of ['PLACE:bec88ded-6beb-5eb1-b0d2-48ded5277326', 'PLACE:5c393732-36d0-5231-8556-05f40fb04238', 'PLACE:fdee5713-93ba-54d5-92be-3957d4f68828', 'P
  - raw: `{"candidateIds":["PLACE:6b93bb7b-7785-5980-95fa-3bdc41e60ac1","PLACE:fdee5713-93ba-54d5-92be-3957d4f68828","PLACE:6800d098-4d36-5bef-b886-dd9fa8765d4d","PLACE:97bf421c-6749-5741-8da1-159231dfb92e","PLACE:88e2247b-345b-561b-9ebb-7cc86d888406`
- `rank-golden-015-hue-ko#r0` (rank, ko): reasons: 'PLACE:b7ab8d1c-e29f-5fb0-ad57-ac739941b9a7' is not one of ['PLACE:4ec73040-342f-5014-877a-584346d731f5', 'PLACE:18caaf23-f9fe-5f9c-938d-04f3de1ff2b4', 'PLACE:d38ec69f-a69c-5bd9-9b7d-92861e719d42', 'B
  - raw: `{"candidateIds":["PLACE:83557320-9db2-5438-9423-c2b44251c70d","PLACE:18caaf23-f9fe-5f9c-938d-04f3de1ff2b4","PLACE:4ec73040-342f-5014-877a-584346d731f5","PLACE:1d69fad5-6e1f-5ac2-bcba-d4d0f93431b4","BOOKING:b7ab8d1c-e29f-5fb0-ad57-ac739941b9`
- `rank-golden-017-sa-en#r0` (rank, en): reasons: 'PLACE:8858d080-bfd6-5d98-a66f-18357b96c3dd' is not one of ['PLACE:53492927-5bbb-54c7-b50c-7e9e0b65c68d', 'PLACE:d915a2e9-87fe-5f58-b056-5dfee69cdf35', 'PLACE:eb9beedb-2282-572d-89bc-2e7d556066bb', 'P
  - raw: `{"candidateIds":["PLACE:eb9beedb-2282-572d-89bc-2e7d556066bb","BOOKING:8858d080-bfd6-5d98-a66f-18357b96c3dd","PLACE:3c2a53da-80ad-5d5b-b70b-72bf19ae9442","PLACE:53492927-5bbb-54c7-b50c-7e9e0b65c68d","PLACE:4021ca88-1d19-5235-84cd-7056ab03cd`
- `rank-golden-020-ha-vi#r0` (rank, vi): reasons: 'PLACE:eaec339e-5aae-590a-8fc8-7c1b69c819eb' is not one of ['PLACE:3525e6f9-fb47-5680-9852-cd385fc80787', 'PLACE:19569031-1379-54dc-bf07-87bcf24a0a3e', 'PLACE:4b5997cd-19a0-5872-b2ff-ece7473c572b', 'P
  - raw: `{"candidateIds":["PLACE:4b5997cd-19a0-5872-b2ff-ece7473c572b","PLACE:3525e6f9-fb47-5680-9852-cd385fc80787","BOOKING:eaec339e-5aae-590a-8fc8-7c1b69c819eb","PLACE:e5b27724-58c5-5a1e-b7d3-bfb4cc409702","PLACE:d6852de1-1e86-56ef-a480-21fd5944d8`
- `rank-golden-023-da-ko#r0` (rank, ko): reasons: 'PLACE:0ad1b3ae-cfe4-5fbe-a56d-9fe472f1b66d' is not one of ['PLACE:a881fe78-d84b-5ef3-8e93-fda654bf9506', 'PLACE:43d5aac3-421b-5073-bdde-b130de47f62a', 'PLACE:4f9d4c51-2d4e-525c-a259-5fac1e1841c9', 'P
  - raw: `{"candidateIds":["PLACE:652e5f9c-25d3-5528-ae45-905bf3f20af7","PLACE:e49f8b62-8db1-5a46-ac62-a54bb685e6be","PLACE:63103ef8-d904-549c-af6d-55cb1ee60a71","PLACE:21113b9c-6873-57ed-a50b-c44c9aec89dc","PLACE:f242559e-1ef1-5d81-ac14-ac58fe73bcbf`
- `rank-golden-025-hue-en#r0` (rank, en): reasons: 'PLACE:b7ab8d1c-e29f-5fb0-ad57-ac739941b9a7' is not one of ['PLACE:18caaf23-f9fe-5f9c-938d-04f3de1ff2b4', 'PLACE:83557320-9db2-5438-9423-c2b44251c70d', 'PLACE:d38ec69f-a69c-5bd9-9b7d-92861e719d42', 'P
  - raw: `{"candidateIds":["PLACE:d38ec69f-a69c-5bd9-9b7d-92861e719d42","PLACE:83557320-9db2-5438-9423-c2b44251c70d","PLACE:18caaf23-f9fe-5f9c-938d-04f3de1ff2b4","PLACE:4ec73040-342f-5014-877a-584346d731f5","PLACE:1d69fad5-6e1f-5ac2-bcba-d4d0f93431b4`
- `rank-golden-033-da-en#r0` (rank, en): reasons: 'PLACE:0ad1b3ae-cfe4-5fbe-a56d-9fe472f1b66d' is not one of ['PLACE:f242559e-1ef1-5d81-ac14-ac58fe73bcbf', 'PLACE:63103ef8-d904-549c-af6d-55cb1ee60a71', 'PLACE:e49f8b62-8db1-5a46-ac62-a54bb685e6be', 'P
  - raw: `{"candidateIds":["PLACE:652e5f9c-25d3-5528-ae45-905bf3f20af7","PLACE:21113b9c-6873-57ed-a50b-c44c9aec89dc","PLACE:63103ef8-d904-549c-af6d-55cb1ee60a71","PLACE:e49f8b62-8db1-5a46-ac62-a54bb685e6be","PLACE:f242559e-1ef1-5d81-ac14-ac58fe73bcbf`
- `order-golden-008-phu-ru#r0` (order, ru): candidateIds: ['PLACE:2a5f04a1-e2ff-579f-b5de-57ed5b2dd1b9', 'PLACE:a00dc094-5a25-50fd-8105-f3c478e24b7b', 'PLACE:de5e8ffd-a3cc-5e5d-9c3f-9172aa6e18f0', 'PLACE:6330321c-6248-50b5-9417-1b51f91d0835'] is too short
  - raw: `{"candidateIds":["PLACE:2a5f04a1-e2ff-579f-b5de-57ed5b2dd1b9","PLACE:a00dc094-5a25-50fd-8105-f3c478e24b7b","PLACE:de5e8ffd-a3cc-5e5d-9c3f-9172aa6e18f0","PLACE:6330321c-6248-50b5-9417-1b51f91d0835"]}`
- `order-golden-009-ha-vi#r0` (order, vi): candidateIds: ['PLACE:3525e6f9-fb47-5680-9852-cd385fc80787', 'BOOKING:eaec339e-5aae-590a-8fc8-7c1b69c819eb', 'PLACE:d6852de1-1e86-56ef-a480-21fd5944d8af', 'PLACE:4b5997cd-19a0-5872-b2ff-ece7473c572b', 'PLACE:6f793e
  - raw: `{"candidateIds":["PLACE:3525e6f9-fb47-5680-9852-cd385fc80787","BOOKING:eaec339e-5aae-590a-8fc8-7c1b69c819eb","PLACE:d6852de1-1e86-56ef-a480-21fd5944d8af","PLACE:4b5997cd-19a0-5872-b2ff-ece7473c572b","PLACE:6f793ed3-01f3-52d8-aed5-6e0ccfdbc3`
- `order-golden-014-hue-en#r0` (order, en): candidateIds: ['PLACE:83557320-9db2-5438-9423-c2b44251c70d', 'PLACE:d38ec69f-a69c-5bd9-9b7d-92861e719d42', 'PLACE:18caaf23-f9fe-5f9c-938d-04f3de1ff2b4', 'BOOKING:b7ab8d1c-e29f-5fb0-ad57-ac739941b9a7'] is too short
  - raw: `{"candidateIds":["PLACE:83557320-9db2-5438-9423-c2b44251c70d","PLACE:d38ec69f-a69c-5bd9-9b7d-92861e719d42","PLACE:18caaf23-f9fe-5f9c-938d-04f3de1ff2b4","BOOKING:b7ab8d1c-e29f-5fb0-ad57-ac739941b9a7"]}`

## Quality misses (24)

- `tips-edge-single-candidate#r0` — tips_max_120_chars
- `tips-edge-injection-description#r0` — tips_max_120_chars
- `tips-edge-injection-preferences#r0` — tips_max_120_chars
- `tips-edge-special-characters#r0` — tips_max_120_chars
- `tips-edge-null-fields#r0` — tips_max_120_chars
- `tips-edge-prefs-language-differs-from-locale#r0` — tips_max_120_chars
- `tips-edge-unsupported-locale-fr#r0` — tips_max_120_chars
- `tips-edge-empty-preferences-string#r0` — tips_max_120_chars
- `tips-edge-hindi-locale#r0` — tips_max_120_chars
- `order-golden-004-hue-ko#r0` — route_within_1_6x_nearest_neighbor (model 23.3 km vs NN 14.4 km)
- `order-golden-005-da-th#r0` — route_within_1_6x_nearest_neighbor (model 48.3 km vs NN 26.9 km)
- `order-golden-008-phu-ru#r0` — route_within_1_6x_nearest_neighbor (model 39.8 km vs NN 20.3 km)
- `order-golden-011-hcm-hi#r0` — route_within_1_6x_nearest_neighbor (model 99.9 km vs NN 53.1 km)
- `order-golden-013-hoi-th#r0` — route_within_1_6x_nearest_neighbor (model 9.4 km vs NN 5.3 km)
- `order-golden-018-phu-zh-TW#r0` — route_within_1_6x_nearest_neighbor (model 47.4 km vs NN 25.6 km)
- `order-golden-022-da-en#r0` — route_within_1_6x_nearest_neighbor (model 63.6 km vs NN 34.2 km)
- `order-golden-025-da-vi#r0` — route_within_1_6x_nearest_neighbor (model 40.3 km vs NN 22.8 km)
- `order-golden-028-phu-ko#r0` — route_within_1_6x_nearest_neighbor (model 62.6 km vs NN 25.2 km)
- `tips-golden-003-hue-en#r0` — tips_max_120_chars
- `tips-golden-005-sa-ru#r0` — tips_max_120_chars
- `tips-golden-011-da-en#r0` — tips_max_120_chars
- `tips-golden-014-da-vi#r0` — tips_max_120_chars
- `tips-golden-016-nha-hi#r0` — tips_max_120_chars
- `tips-golden-019-ha-en#r0` — tips_max_120_chars
