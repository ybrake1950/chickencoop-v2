"""
Phase 18: Distributed Tracing Tests
===================================

FUNCTIONALITY BEING TESTED:
---------------------------
- Request correlation IDs
- End-to-end trace collection
- Trace visualization
- Performance bottleneck identification

WHY THIS MATTERS:
-----------------
Distributed tracing helps identify where time is spent in complex
operations. It's essential for debugging performance issues that
span multiple services (Pi → Lambda → S3).

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase18_observability/tracing/test_distributed_tracing.py -v
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.observability.tracing import (
    Tracer,
    Span,
    TraceCollector,
    TraceAnalyzer,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def tracer():
    """Provide a tracer."""
    return Tracer(service_name="chickencoop-pi")


@pytest.fixture
def collector():
    """Provide a trace collector."""
    return TraceCollector()


@pytest.fixture
def analyzer():
    """Provide a trace analyzer."""
    return TraceAnalyzer()


# =============================================================================
# TestCorrelationIDs
# =============================================================================

class TestCorrelationIDs:
    """Test request correlation IDs."""

    def test_correlation_id_generated(self, tracer):
        """Correlation ID generated for requests."""
        span = tracer.start_span("test_operation")
        assert span.trace_id is not None
        assert len(span.trace_id) > 0
        # Should be valid UUID format
        uuid.UUID(span.trace_id)

    def test_correlation_id_propagated(self, tracer):
        """Correlation ID propagated through system."""
        parent = tracer.start_span("parent_operation")
        child = tracer.start_span("child_operation", parent=parent)
        assert child.trace_id == parent.trace_id
        assert child.parent_span_id == parent.span_id

    def test_correlation_id_in_logs(self, tracer, caplog):
        """Correlation ID included in logs."""
        import logging
        caplog.set_level(logging.INFO)
        span = tracer.start_span("logged_operation")
        tracer.log_with_trace(span, "Processing request")
        assert span.trace_id in caplog.text

    def test_correlation_id_in_responses(self, tracer):
        """Correlation ID returned in responses."""
        span = tracer.start_span("api_request")
        headers = tracer.get_response_headers(span)
        assert "X-Trace-Id" in headers
        assert headers["X-Trace-Id"] == span.trace_id


# =============================================================================
# TestTraceCollection
# =============================================================================

class TestTraceCollection:
    """Test trace collection."""

    def test_trace_spans_created(self, tracer):
        """Trace spans created for operations."""
        span = tracer.start_span("upload_video")
        assert span is not None
        assert span.operation_name == "upload_video"
        assert span.start_time is not None

    def test_span_timing_accurate(self, tracer):
        """Span timing is accurate."""
        span = tracer.start_span("timed_operation")
        tracer.end_span(span)
        assert span.end_time is not None
        assert span.duration_ms >= 0
        assert span.end_time >= span.start_time

    def test_span_includes_metadata(self, tracer):
        """Spans include relevant metadata."""
        span = tracer.start_span(
            "upload_video",
            metadata={"file_size": 1024, "coop_id": "coop-1"}
        )
        assert span.metadata is not None
        assert span.metadata["file_size"] == 1024
        assert span.metadata["coop_id"] == "coop-1"

    @patch("src.observability.tracing.boto3.client")
    def test_traces_sent_to_xray(self, mock_boto, collector, tracer):
        """Traces sent to AWS X-Ray."""
        span = tracer.start_span("test_op")
        tracer.end_span(span)
        collector.submit(span)
        mock_boto.return_value.put_trace_segments.assert_called_once()


# =============================================================================
# TestTraceAnalysis
# =============================================================================

class TestTraceAnalysis:
    """Test trace analysis capabilities."""

    def test_identify_slow_spans(self, analyzer):
        """Slow spans can be identified."""
        spans = [
            Span(operation_name="fast_op", duration_ms=10),
            Span(operation_name="slow_op", duration_ms=5000),
            Span(operation_name="medium_op", duration_ms=200),
        ]
        slow = analyzer.find_slow_spans(spans, threshold_ms=1000)
        assert len(slow) == 1
        assert slow[0].operation_name == "slow_op"

    def test_identify_error_spans(self, analyzer):
        """Error spans can be identified."""
        spans = [
            Span(operation_name="success_op", error=None),
            Span(operation_name="failed_op", error="ConnectionTimeout"),
            Span(operation_name="another_success", error=None),
        ]
        errors = analyzer.find_error_spans(spans)
        assert len(errors) == 1
        assert errors[0].operation_name == "failed_op"
        assert errors[0].error == "ConnectionTimeout"

    def test_trace_visualization(self, analyzer):
        """Traces can be visualized."""
        spans = [
            Span(operation_name="parent", duration_ms=500, span_id="1", parent_span_id=None),
            Span(operation_name="child_a", duration_ms=200, span_id="2", parent_span_id="1"),
            Span(operation_name="child_b", duration_ms=250, span_id="3", parent_span_id="1"),
        ]
        viz = analyzer.visualize(spans)
        assert viz is not None
        assert viz.root_span.operation_name == "parent"
        assert len(viz.root_span.children) == 2
