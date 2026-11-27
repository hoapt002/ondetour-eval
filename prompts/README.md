# Prompts

Mỗi thư mục `vN/` là một phiên bản prompt. `v1` sao chép **nguyên văn** prompt đang chạy ở backend
(`goroute` → `AiTripServiceImpl` + `AiTripLanguageSupport.claudeLanguageRule()`).

Cách ghép giống hệt Java:

```
system = common/system_context.txt + <task>/system.txt + "\n" + common/language_rule.txt
user   = <task>/user.txt   (biến dạng ${name}, thay bằng string.Template)
```

Đổi prompt: copy `v1` sang `v2`, sửa, rồi chạy `ondetour-eval run --prompt-version v2`.
Prompt hash nằm trong cache key nên mọi thay đổi chữ đều buộc gọi lại model.
