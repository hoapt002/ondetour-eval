# ondetour-eval

Bộ đánh giá hồi quy cho các prompt LLM của tính năng **AI tạo lịch trình** trong OnDetour
(backend `goroute` → `AiTripServiceImpl`). Chạy lại mỗi khi đổi prompt hoặc đổi model; cổng chặn là
**≥ 98% đầu ra hợp lệ theo JSON Schema**.

## Đánh giá cái gì

Backend gọi Claude ở 3 chỗ, mỗi chỗ phải trả về JSON:

| Task | Hàm backend | JSON mong đợi |
|---|---|---|
| `rank` | `rankCandidatesWithClaude` | `{"candidateIds":[…],"reasons":{id: text}}` |
| `order` | `orderByClaudeOrDistance` | `{"candidateIds":[…]}` — đúng một hoán vị của input |
| `tips` | `generateVisitTips` | `{"tips":{id: text ≤160 ký tự}}` — đủ mọi ID |

`prompts/v1/` là bản sao **nguyên văn** prompt trên backend, ghép giống hệt Java
(`AI_TRIP_SYSTEM_CONTEXT + block + "\n" + claudeLanguageRule()`), candidate được serialize như
Jackson (thứ tự field của `AiTripCandidateResponse`, giữ `null`).

## Dataset (155 tình huống)

- `datasets/golden.jsonl` — 94 case: 10 thành phố thật (Hà Nội, TP.HCM, Đà Nẵng, Hội An, Huế, Đà Lạt,
  Sa Pa, Nha Trang, Phú Quốc, Hạ Long) × 8 tháng (đủ mùa khô/mưa/lũ/lạnh) × 3 pace × 8 locale
  (`en vi ko ja zh-TW th ru hi`), địa điểm và booking thật từ `data/places.json`.
- `datasets/edge_cases.jsonl` — 61 case: 1 và 2 ứng viên, 60 ứng viên (ngữ cảnh dài), toàn khách sạn,
  toàn quán ăn, ID trùng trong input, prompt injection (trong mô tả và trong preferences), ký tự đặc biệt
  (ngoặc kép, `\`, xuống dòng, emoji, ``` ), field `null`, mô tả rất dài, ngôn ngữ preferences khác locale,
  locale không hỗ trợ (`fr`), toạ độ trùng nhau, điểm ngoài thành phố, 1 ngày dày đặc, 14 ngày thưa,
  qua năm mới, preferences rỗng / không dấu / emoji-slang, mùa lũ miền Trung, booking giá USD.

Dataset sinh tất định từ `scripts/build_dataset.py` (seed cố định, ID `uuid5`). Test
`test_dataset_is_reproducible` chặn việc sửa tay file `.jsonl` mà quên cập nhật script.

## Chấm điểm

**Cổng (gate) — `schema_valid`:** parse output đúng như backend (`extractJson`: từ `{` đầu tới `}` cuối,
rồi Jackson), sau đó validate với schema trong `schemas/` **được siết theo từng case**:

- `rank`: mọi ID phải thuộc input, không trùng; key của `reasons` phải thuộc input.
- `order`: đúng N ID, không trùng, toàn bộ thuộc input (tức một hoán vị).
- `tips`: đủ mọi ID input, không ID lạ, mỗi tip 1–160 ký tự.

Lỗi provider (timeout, hết quota) cũng tính là **trượt** — không lờ đi.

**Chất lượng (báo cáo, không chặn):** strict JSON (không có chữ thừa / ``` fence), rank phủ đủ ứng viên,
khách sạn không nằm top 3, ≥80% ID có lý do, ngôn ngữ đúng locale (nhận dạng theo bảng chữ, đã loại tên
riêng tiếng Việt), tip ≤120 ký tự, không câu sáo rỗng, không chép mô tả, lộ trình không dài hơn 1.6×
nearest-neighbor, không bị prompt injection.

## Chạy

```bash
uv sync
```

Máy dev (dùng Claude Code CLI đã đăng nhập, không cần API key):

```bash
uv run ondetour-eval run --model claude-haiku-5-5
```

Giống production nhất (Messages API, đúng payload `ClaudeClient`, `max_tokens=2500`):

```bash
ANTHROPIC_API_KEY=... uv run ondetour-eval run --provider anthropic --model claude-haiku-5-5
```

Các lệnh khác:

```bash
uv run ondetour-eval list                                   # đếm case
uv run ondetour-eval render tips-edge-special-characters    # xem prompt thật của 1 case
uv run ondetour-eval run --task tips --category edge        # lọc
uv run ondetour-eval run --repeats 3                        # đo độ chập chờn
uv run ondetour-eval compare runs/<cũ> runs/<mới>           # so 2 lần chạy, liệt kê case hỏng/được sửa
uv run pytest -q && uv run ruff check .                     # test offline của chính bộ chấm
```

Mỗi lần chạy ghi `runs/<thời gian>_<prompt>_<model>/` gồm `results.jsonl` (raw output + điểm từng case),
`summary.json`, `report.md`. Exit code 1 khi dưới ngưỡng. Output được cache theo
`hash(provider, model, system, user, repeat)` — đổi 1 chữ trong prompt hoặc đổi model là gọi lại; giữ
nguyên thì chạy lại tức thì (dùng `--no-cache` để ép gọi lại).

## Quy trình đổi prompt / model

1. Copy `prompts/v1` → `prompts/v2`, sửa.
2. `uv run ondetour-eval run --prompt-version v2 --label v2-haiku`
3. `uv run ondetour-eval compare runs/baselines/<baseline> runs/v2-haiku`
4. Đạt ≥98% và không có regression → port prompt sang `AiTripServiceImpl` ở backend.

Đổi model: giữ prompt, đổi `--model`. CI (`.github/workflows/eval.yml`) tự chạy khi PR đụng `prompts/`,
`schemas/`, `datasets/`, `src/`; chạy tay qua *Run workflow* để chọn model / prompt version. Cần secret
`ANTHROPIC_API_KEY`.

## Kết quả hiện tại (claude-haiku-5-5, 155 case, 2026-11-27)

| Prompt | Schema-valid | Parse được | Strict JSON | Ghi chú |
|---|---:|---:|---:|---|
| `v1` (đang chạy trên production) | 87.7% ❌ | 96.8% | 92.3% | rank 77%, order 89%, tips 100% |
| `v2` (chỉ sửa chữ) | 84.5% ❌ | 97.4% | 97.4% | order sửa xong, rank còn đổi `BOOKING:`→`PLACE:` |
| `v3` (v2 + ID ngắn `c1…cN`) | **99.4% ✅** | 100% | 100% | còn 1 tip thừa ID `c9` |

Lỗi của `v1`, tất cả đều là lỗi thật trên production (backend lặng lẽ fallback, mất kết quả AI):

1. `rank`: model đổi `BOOKING:<uuid>` thành `PLACE:<uuid>` trong key của `reasons`.
2. `rank`: JSON hỏng khi lý do dài — có key không có giá trị (`"id1","id2":"…"`).
3. `order`: model **bỏ bớt** địa điểm vì luật "max N stops/day" và "keep only one ACCOMMODATION per day"
   mâu thuẫn với "same candidates, reordered".
4. `tips` (chất lượng): system ghi tối đa 160 ký tự, user ghi 120 → chỉ 69% tip ≤120 ký tự.

`v3` gửi ID ngắn và bỏ các field chứa UUID (`sourceId`, `bookingId`, `photoUrl`); backend chỉ cần map
`cN → id thật` ở 3 chỗ parse (`applyRankResult`, `parseCandidateOrder`, `parseVisitTips`). Bật bằng
`prompts/v3/config.json` (`"id_mode": "alias"`). Baseline lưu ở `runs/baselines/`.

Còn mở: `tips` của `v2`/`v3` có 4/48 case viết tiếng Việt thay vì `ru`/`zh-TW` (v1 đúng 100%).
