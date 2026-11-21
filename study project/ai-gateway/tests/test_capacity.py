"""KV-cache sizing: 32L/8H/128/1/8192 fp16 ~= 1 GiB."""

from gateway.capacity import kv_cache_bytes


def test_kv_cache_8k_context_is_about_1gib() -> None:
    n = kv_cache_bytes(layers=32, kv_heads=8, d_head=128, batch=1,
                       seq_len=8192, bytes_per_value=2)
    assert n == 1073741824  # exactly 1 GiB
    assert abs(n / (1024**3) - 1.0) < 0.01


def test_kv_cache_scales_linearly() -> None:
    base = kv_cache_bytes(32, 8, 128, 1, 8192)
    assert kv_cache_bytes(32, 8, 128, 4, 8192) == 4 * base
    assert kv_cache_bytes(32, 8, 128, 1, 16384) == 2 * base
