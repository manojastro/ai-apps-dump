import pytest

from packages.connectors.provider import validate_endpoint
from packages.connectors.replay import ConnectorError, ReplayConnector, snapshot


def test_provider_metadata_destination_is_always_blocked():
    with pytest.raises(ValueError, match="DESTINATION"):
        validate_endpoint("http://169.254.169.254/v1", {"169.254.169.254"}, {"169.254.169.254"})


def test_provider_cannot_follow_unapproved_host():
    with pytest.raises(ValueError, match="DESTINATION"):
        validate_endpoint("https://unapproved.invalid/v1", {"api.openai.com"}, set())


def test_arbitrary_tool_parameters_denied():
    with pytest.raises(ConnectorError, match="SCOPE"):
        ReplayConnector(snapshot()).call("query_metrics", "run", {"query": "arbitrary_promql"})


def test_connector_error_normalized():
    packet = snapshot()
    packet["traces"] = {"error": "TIMEOUT"}
    with pytest.raises(ConnectorError, match="TIMEOUT"):
        ReplayConnector(packet).call("search_traces", "run")
