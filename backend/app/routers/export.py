"""Export routes for generating downloadable linguistic data files."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.database import get_db_dependency
from app.services.neo4j_service import (
    Neo4jExportDataError,
    get_file_graph_data,
)
from app.services.export_flextext_service import generate_flextext_xml


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


class FlexTextExportRequest(BaseModel):
    """Request body for triggering a FLEXText export."""

    file_id: str


@router.post("/flextext", response_class=Response)
async def export_flextext(
    payload: FlexTextExportRequest, db=Depends(get_db_dependency)
) -> Response:
    """Return a FLEXText export for the requested dataset."""

    file_id = payload.file_id.strip()
    if not file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_id must be a non-empty string",
        )

    try:
        graph_data = get_file_graph_data(file_id, db)
    except Neo4jExportDataError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.exception("Failed to retrieve graph data for export", extra={"file_id": file_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve export data",
        ) from exc

    try:
        xml_payload = generate_flextext_xml(graph_data)
    except Exception as exc:  # pragma: no cover - unexpected generation issue
        logger.exception("Failed to generate FLEXText XML", extra={"file_id": file_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate FLEXText export",
        ) from exc

    headers = {
        "Content-Disposition": "attachment; filename=\"export.flextext\"",
        "X-Lexiconnect-Export": "flextext",
    }

    return Response(content=xml_payload, media_type="application/xml", headers=headers)
"""Export routes for generating downloadable linguistic data files."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.database import get_db_dependency
from app.services.neo4j_service import (
    Neo4jExportDataError,
    get_file_graph_data,
)
from app.services.export_flextext_service import generate_flextext_xml


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


class FlexTextExportRequest(BaseModel):
    """Request body for triggering a FLEXText export."""

    file_id: str


@router.post("/flextext", response_class=Response)
async def export_flextext(
    payload: FlexTextExportRequest, db=Depends(get_db_dependency)
) -> Response:
    """Return a FLEXText export for the requested dataset."""

    file_id = payload.file_id.strip()
    if not file_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file_id must be a non-empty string",
        )

    try:
        graph_data = get_file_graph_data(file_id, db)
    except Neo4jExportDataError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.exception("Failed to retrieve graph data for export", extra={"file_id": file_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve export data",
        ) from exc

    try:
        xml_payload = generate_flextext_xml(graph_data)
    except Exception as exc:  # pragma: no cover - unexpected generation issue
        logger.exception("Failed to generate FLEXText XML", extra={"file_id": file_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate FLEXText export",
        ) from exc

    headers = {
        "Content-Disposition": "attachment; filename=\"export.flextext\"",
        "X-Lexiconnect-Export": "flextext",
    }

    return Response(content=xml_payload, media_type="application/xml", headers=headers)

