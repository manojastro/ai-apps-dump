"""Synthetic event producer for the demo shop.

    uv run python demo_pipeline/producers/produce.py               # write JSONL landing files
    uv run python demo_pipeline/producers/produce.py --kafka localhost:9092 --registry http://localhost:8081

Default output: demo_pipeline/data/<topic>.jsonl (fixed seed, so output is reproducible).
The Kafka path needs `schemaguard[kafka]` and the compose `core` profile; it was written but not
verified on the build machine (no Docker there).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from schemaguard.pipeline.generator import generate_all, write_jsonl
from schemaguard.schemas.avro import load_pipeline_schemas

PIPELINE_DIR = Path(__file__).resolve().parents[1]


def produce_to_kafka(events: dict, bootstrap: str, registry_url: str) -> None:
    import json

    from confluent_kafka import Producer
    from confluent_kafka.schema_registry import SchemaRegistryClient
    from confluent_kafka.schema_registry.avro import AvroSerializer
    from confluent_kafka.serialization import MessageField, SerializationContext

    sr = SchemaRegistryClient({"url": registry_url})
    producer = Producer({"bootstrap.servers": bootstrap})
    for topic, rows in events.items():
        schema_str = (PIPELINE_DIR / "avro" / f"{topic}.avsc").read_text(encoding="utf-8")
        ser = AvroSerializer(sr, schema_str)
        for r in rows:
            producer.produce(topic, value=ser(r, SerializationContext(topic, MessageField.VALUE)))
            producer.poll(0)
        producer.flush(30)
        print(f"produced {len(rows)} events to {topic}")
    _ = json  # keep import local for optional path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--out", type=Path, default=PIPELINE_DIR / "data")
    ap.add_argument("--kafka", default="", help="bootstrap servers; if set, also produce to Kafka")
    ap.add_argument("--registry", default="http://localhost:8081")
    args = ap.parse_args()

    schemas = load_pipeline_schemas(PIPELINE_DIR / "avro")
    events = generate_all(schemas, seed=args.seed, scale=args.scale)
    paths = write_jsonl(events, args.out)
    for topic, p in paths.items():
        print(f"{topic}: {len(events[topic])} events -> {p}")
    if args.kafka:
        produce_to_kafka(events, args.kafka, args.registry)


if __name__ == "__main__":
    main()
