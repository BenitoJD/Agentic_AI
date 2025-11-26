"""File upload routes."""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException

from ..services.file_extractor import EXTRACTORS, extract_text
from ..services.vector_store import ingest_text, list_files

router = APIRouter(prefix="/api/files")


@router.get("")
async def list_uploaded_files() -> list[dict]:
    """Return a summary of files currently stored in the vector database."""
    return list_files()


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    raw = await file.read()
    try:
        text = extract_text(file.filename, raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - safety net
        raise HTTPException(status_code=500, detail=f"Failed to process file: {exc}") from exc

    chunks = ingest_text(text, metadata={"filename": file.filename})
    return {
        "status": "ok",
        "filename": file.filename,
        "chunks": chunks,
        "supportedTypes": sorted(EXTRACTORS.keys()),
    }

