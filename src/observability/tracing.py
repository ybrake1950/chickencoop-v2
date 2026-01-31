"""Distributed tracing for the chicken coop system."""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """A single span in a distributed trace."""

    operation_name: str = ""
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    children: List["Span"] = field(default_factory=list)


class Tracer:
    """Creates and manages trace spans."""

    def __init__(self, service_name: str = ""):
        self.service_name = service_name

    def start_span(
        self,
        operation_name: str,
        parent: Optional[Span] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Span:
        """Create and start a new span, optionally as a child of a parent span."""
        trace_id = parent.trace_id if parent else str(uuid.uuid4())
        parent_span_id = parent.span_id if parent else None
        return Span(
            operation_name=operation_name,
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            start_time=datetime.now(timezone.utc),
            metadata=metadata,
        )

    def end_span(self, span: Span) -> None:
        """End a span by recording the finish time and computing duration."""
        span.end_time = datetime.now(timezone.utc)
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000

    def log_with_trace(self, span: Span, message: str) -> None:
        """Log a message with the span's trace ID for correlation."""
        logger.info("[trace_id=%s] %s", span.trace_id, message)

    def get_response_headers(self, span: Span) -> Dict[str, str]:
        """Return HTTP headers containing the trace ID for response propagation."""
        return {"X-Trace-Id": span.trace_id}


class TraceCollector:
    """Submits completed spans to AWS X-Ray."""

    def submit(self, span: Span) -> None:
        """Submit a completed span to AWS X-Ray as a trace segment."""
        client = boto3.client("xray")
        segment = {
            "name": span.operation_name,
            "id": span.span_id[:16],
            "trace_id": span.trace_id,
            "start_time": span.start_time.timestamp() if span.start_time else 0,
            "end_time": span.end_time.timestamp() if span.end_time else 0,
        }
        client.put_trace_segments(TraceSegmentDocuments=[json.dumps(segment)])


@dataclass
class TraceVisualization:
    """Tree visualization of a trace."""

    root_span: Span


class TraceAnalyzer:
    """Analyzes collected trace spans."""

    def find_slow_spans(self, spans: List[Span], threshold_ms: float = 1000) -> List[Span]:
        """Return spans whose duration exceeds the given threshold in milliseconds."""
        return [s for s in spans if s.duration_ms is not None and s.duration_ms >= threshold_ms]

    def find_error_spans(self, spans: List[Span]) -> List[Span]:
        """Return spans that have an error recorded."""
        return [s for s in spans if s.error is not None]

    def visualize(self, spans: List[Span]) -> TraceVisualization:
        """Build a parent-child tree from a flat list of spans for visualization."""
        span_map: Dict[str, Span] = {}
        root = None
        for s in spans:
            s.children = []
            span_map[s.span_id] = s
            if s.parent_span_id is None:
                root = s

        for s in spans:
            if s.parent_span_id and s.parent_span_id in span_map:
                span_map[s.parent_span_id].children.append(s)

        return TraceVisualization(root_span=root)
