# Plan: Parallelize DeepSeek API Calls + Shorter Comments

## Problem

Comment generation for each chapter is **100% sequential** — one API call at a time.

With `comment_frequency = 5` and ~200 sentences per chapter:
- **40 sequential** DeepSeek API calls
- Each call takes 3-10 seconds
- **Total: 2-7 minutes per chapter** just for comments
- User reports 10+ minutes already for chapter 4

## Changes

### 1. Parallelize API calls in `generate_all()` — [`src/core/comment_manager.py`](src/core/comment_manager.py)

Replace sequential loop with `asyncio.gather()` + `asyncio.Semaphore(max_concurrent=5)`:

```python
# Before:
for group in groups:
    comment = await generate_comment(...)  # sequential wait

# After:
sem = asyncio.Semaphore(5)
results = await asyncio.gather(*[limited_gen(...) for ...])
```

**Safe** because comments are independent — context is built from original sentences only.

**Expected:** 40 sequential calls × 5s = 200s → ~40s with 5 concurrent.

### 2. Shorter comments — [`src/core/comment_manager.py`](src/core/comment_manager.py)

- Change prompt in `generate_comment()` (line 99-101): make it stricter about 1-2 sentences
- Lower `max_tokens` from 300 to 150 in `_call_api()` (line 217)

Current prompt: `"Дай короткий ёмкий комментарий (1-3 предложения):\n\n{context}"`
New prompt: `"Напиши короткий комментарий (1-2 предложения, максимум 3):\n\n{context}"`

### 3. Edge TTS — already resilient

Already in place:
- Retry 3× with exponential backoff (2→4→8s) in [`synthesize_segment()`](src/core/tts_manager.py:115-161)
- `asyncio.wait_for(timeout=120)` — won't hang indefinitely
- Checkpoint per completed chapter
- DNS/timeout/503 errors all caught by retry patterns

## Files to Modify

| File | Change |
|------|--------|
| [`src/core/comment_manager.py`](src/core/comment_manager.py) | Add `max_concurrent` to `CommentConfig` (5), parallelize `generate_all()`, shorter prompt, `max_tokens` → 150 |
| [`src/config/defaults.toml`](src/config/defaults.toml) | Add `max_concurrent = 5` |
