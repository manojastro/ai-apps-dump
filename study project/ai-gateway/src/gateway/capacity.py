"""KV-cache sizing math (interview favourite)."""


def kv_cache_bytes(
    layers: int,
    kv_heads: int,
    d_head: int,
    batch: int,
    seq_len: int,
    bytes_per_value: int = 2,
) -> int:
    """Bytes = 2 (K and V) * bytes_per_value * layers * kv_heads * d_head
    * batch * seq_len."""
    return 2 * bytes_per_value * layers * kv_heads * d_head * batch * seq_len
