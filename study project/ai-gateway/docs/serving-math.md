# Serving math (learner-written, M9)

KV cache = the memory a model keeps about the tokens it has already read, so
it does not re-read them for every new word. Think of it like keeping the
ticket history open on your desk instead of re-opening it for every reply.

## Formula
bytes = 2 (Key + Value) x bytes_per_value x layers x kv_heads x d_head x batch x seq_len

## Worked example
32 layers, 8 KV heads, d_head 128, batch 1, 8192 tokens, fp16 (2 bytes):
2 x 2 x 32 x 8 x 128 x 1 x 8192 = 1,073,741,824 bytes = exactly 1 GiB.

## Why this matters
- Longer context costs more memory in a straight line: 16k tokens = 2x the
  memory of 8k. Long chats on many users can fill the GPU fast.
- Bigger batches also scale linearly: 4 users at once = 4x the cache.
- GQA (grouped-query attention) shares KV heads between query heads, so
  kv_heads is small (e.g. 8 instead of 32) and the cache shrinks by the same
  ratio. Less memory per request = more requests per GPU.
- Time-to-first-token waits on reading the whole prompt; tokens-per-second
  after that is limited by re-reading the growing cache, which is why output
  tokens feel slower than input tokens.

Checked by `tests/test_capacity.py`. See `src/gateway/capacity.py`.
