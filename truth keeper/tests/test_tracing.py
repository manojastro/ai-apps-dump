from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app import tracing
from app.core.detection import detect_dir
from app.core.proposer import propose
from app.llm.client import LLMClient


def test_pipeline_steps_and_llm_calls_are_traced(dataset):
    root, _, _ = dataset
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracing.use_provider(provider)
    try:
        conflict = detect_dir(root).conflicts[0]
        propose(conflict, LLMClient(), "v2")
    finally:
        tracing.use_provider(None)
    spans = {s.name: s for s in exporter.get_finished_spans()}
    for name in ("detection.run", "adapters.read_all", "matcher.match", "detector.detect", "proposer.propose",
                 "llm.call"):
        assert name in spans, name
    llm = spans["llm.call"].attributes
    assert llm["openinference.span.kind"] == "LLM"
    assert llm["tk.prompt_version"] == "v2" and llm["llm.model_name"] == "mock-clean"
    assert "input.value" in llm and "output.value" in llm
    assert llm["llm.token_count.prompt"] > 0 and "tk.latency_ms" in llm
    prop = spans["proposer.propose"].attributes
    assert prop["tk.conflict_id"] == conflict.id and prop["tk.status"] == "PENDING_REVIEW"
    assert prop["tk.first_try_valid"] is True


def test_tracing_disabled_without_endpoint():
    assert tracing.setup_tracing(None) is False
