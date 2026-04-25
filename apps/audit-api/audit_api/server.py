"""Small stdlib HTTP helpers for the mock audit API."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, urlparse

from audit_api.mock_service import AuditMockService


def format_sse_event(event: dict[str, Any]) -> str:
    return f"event: {event['type']}\ndata: {json.dumps(event, sort_keys=True)}\n\n"


class AuditApiHandler(BaseHTTPRequestHandler):
    service = AuditMockService()

    @classmethod
    def with_service(cls, service: AuditMockService) -> type["AuditApiHandler"]:
        class BoundAuditApiHandler(cls):
            pass

        BoundAuditApiHandler.service = service
        return BoundAuditApiHandler

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        content_length = int(self.headers.get("content-length", "0"))
        if content_length == 0:
            return {}
        raw_body = self.rfile.read(content_length)
        body = json.loads(raw_body.decode("utf-8"))
        if not isinstance(body, dict):
            raise ValueError("request body must be a JSON object")
        return body

    def _send_json(self, status: int, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status: int, code: str, message: str) -> None:
        self._send_json(
            status,
            {
                "code": code,
                "message": message,
                "requestId": "mock_request",
                "details": {"path": self.path},
            },
        )

    def _send_sse(self, events: list[dict[str, Any]]) -> None:
        body = "".join(format_sse_event(event) for event in events).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/event-stream")
        self.send_header("cache-control", "no-cache")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == "/api/projects":
            self._send_json(200, self.service.list_projects())
            return
        if path == "/api/findings":
            analysis_id = parse_qs(parsed_url.query).get("analysisId", [""])[0]
            try:
                self._send_json(200, self.service.list_findings(analysis_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/projects/"):
            project_id = path.removeprefix("/api/projects/")
            try:
                self._send_json(200, self.service.get_project(project_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/samples/"):
            sample_id = path.removeprefix("/api/samples/")
            try:
                self._send_json(200, self.service.get_sample(sample_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/artifacts/"):
            artifact_id = path.removeprefix("/api/artifacts/")
            try:
                self._send_json(200, self.service.get_artifact(artifact_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/reports/"):
            report_id = path.removeprefix("/api/reports/")
            try:
                self._send_json(200, self.service.get_report(report_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/analyses/") and path.endswith("/events"):
            analysis_id = path.removeprefix("/api/analyses/").removesuffix("/events")
            try:
                self._send_sse(self.service.list_events(analysis_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/analyses/") and path.endswith("/state"):
            analysis_id = path.removeprefix("/api/analyses/").removesuffix("/state")
            try:
                self._send_json(200, self.service.get_analysis_state(analysis_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/analyses/") and path.endswith("/interrupts"):
            analysis_id = path.removeprefix("/api/analyses/").removesuffix("/interrupts")
            try:
                self._send_json(200, self.service.list_approvals(analysis_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        if path.startswith("/api/analyses/"):
            analysis_id = path.removeprefix("/api/analyses/")
            try:
                self._send_json(200, self.service.get_analysis(analysis_id))
            except KeyError as exc:
                self._send_error(404, "not_found", str(exc))
            return
        self._send_error(404, "not_found", "mock route not implemented")

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path.startswith("/api/findings/"):
                finding_id = path.removeprefix("/api/findings/")
                self._send_json(200, self.service.patch_finding(finding_id, payload))
                return
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_error(400, "bad_request", str(exc))
            return
        self._send_error(404, "not_found", "mock route not implemented")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/projects":
                self._send_json(201, self.service.create_project(payload))
                return
            if path == "/api/samples:upload":
                self._send_json(201, self.service.upload_sample(payload))
                return
            if path == "/api/analyses":
                self._send_json(201, self.service.create_analysis(payload))
                return
            if path == "/api/reports":
                self._send_json(201, self.service.create_report(payload))
                return
            if path.startswith("/api/analyses/") and path.endswith("/runs:resume"):
                analysis_id = path.removeprefix("/api/analyses/").removesuffix(
                    "/runs:resume"
                )
                self._send_json(200, self.service.resume_run(analysis_id))
                return
            if path.startswith("/api/analyses/") and path.endswith("/runs"):
                analysis_id = path.removeprefix("/api/analyses/").removesuffix("/runs")
                self._send_json(200, self.service.start_run(analysis_id))
                return
            decision_route = self._parse_interrupt_decision_path(path)
            if decision_route is not None:
                analysis_id, interrupt_id, status = decision_route
                self._send_json(
                    200,
                    self.service.decide_approval(
                        analysis_id,
                        interrupt_id,
                        status,
                        payload,
                    ),
                )
                return
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_error(400, "bad_request", str(exc))
            return
        self._send_error(404, "not_found", "mock route not implemented")

    @staticmethod
    def _parse_interrupt_decision_path(path: str) -> tuple[str, str, str] | None:
        prefix = "/api/analyses/"
        marker = "/interrupts/"
        if not path.startswith(prefix) or marker not in path:
            return None
        analysis_id, interrupt_action = path.removeprefix(prefix).split(marker, 1)
        if interrupt_action.endswith(":approve"):
            return analysis_id, interrupt_action.removesuffix(":approve"), "approved"
        if interrupt_action.endswith(":reject"):
            return analysis_id, interrupt_action.removesuffix(":reject"), "rejected"
        return None
