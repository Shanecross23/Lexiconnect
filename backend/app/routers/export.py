"""Export routes for generating downloadable linguistic data files."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.database import get_db_dependency
from app.exporters import ExporterNotFoundError, get_exporter
from app.services.neo4j_service import get_all_texts_graph_data


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


class ExportRequest(BaseModel):
    """Request body for triggering a FLEXText export."""

    file_id: str


@router.post("", response_class=Response)
@router.post("/flextext", response_class=Response)
async def export_dataset(
    payload: ExportRequest,
    file_type: str = Query("flextext", alias="file_type"),
    db=Depends(get_db_dependency),
) -> Response:
    """Return a FLEXText export for the requested dataset."""

    file_id = payload.file_id.strip()
    if not file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_id must be a non-empty string",
        )

    try:
        exporter = get_exporter(file_type)
    except ExporterNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    context = {"file_id": file_id, "file_type": exporter.file_type}

    logger.info("Starting export", extra=context)

    try:
        graph_payloads = get_all_texts_graph_data(db)
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.exception("Failed to retrieve graph data for export", extra=context)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve export data",
        ) from exc

    if not graph_payloads:
        message = "No texts available for export"
        logger.warning("Export failed: no texts found", extra={**context, "error": message})
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    try:
        export_payload = exporter.export({"texts": graph_payloads})
    except Exception as exc:  # pragma: no cover - unexpected generation issue
        logger.exception("Failed to serialize export payload", extra=context)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate export output",
        ) from exc

    filename_base = file_id or "export"
    filename = f"{filename_base}.{exporter.file_extension}"
    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"",
        "X-Lexiconnect-Export": exporter.file_type,
    }

    logger.info(
        "Completed export",
        extra={**context, "bytes": len(export_payload)},
    )

    return Response(content=export_payload, media_type=exporter.media_type, headers=headers)

