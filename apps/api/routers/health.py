"""Liveness + readiness probes (ops endpoints, unversioned — monitoring shouldn't
track the API version)."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from apps.api.schemas_responses import HealthResponse, ReadinessResponse
from apps.api.services import analyst_service

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ewl-api")


@router.get("/ready")
def ready(response: Response) -> ReadinessResponse:
    """200 when the analyst is warm, else 503 (holds LB traffic). Never forces a build."""
    prewarmed = analyst_service.is_prewarmed()
    if not prewarmed:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if prewarmed else "not_ready",
        analyst_prewarmed=prewarmed,
        qa_enabled=analyst_service.qa_enabled_setting(),
    )
