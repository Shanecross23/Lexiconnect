from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db_dependency
import uuid

router = APIRouter()


# Pydantic models for documentation
class DocumentCreate(BaseModel):
    title: str
    content: str
    language_id: str = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    language_id: str = None
    created_at: str


@router.post("/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    db=Depends(get_db_dependency),
):
    """Create a new documentation entry"""
    try:
        document_id = str(uuid.uuid4())

        # Create document and optionally link to language
        if document.language_id:
            result = db.run(
                """
                MATCH (l:Language {id: $language_id})
                CREATE (d:Document {
                    id: $id,
                    title: $title,
                    content: $content,
                    created_at: datetime()
                })
                CREATE (d)-[:DOCUMENTS]->(l)
                RETURN d.id as id, d.title as title, d.content as content, 
                       l.id as language_id, toString(d.created_at) as created_at
                """,
                id=document_id,
                title=document.title,
                content=document.content,
                language_id=document.language_id,
            )
        else:
            result = db.run(
                """
                CREATE (d:Document {
                    id: $id,
                    title: $title,
                    content: $content,
                    created_at: datetime()
                })
                RETURN d.id as id, d.title as title, d.content as content, 
                       null as language_id, toString(d.created_at) as created_at
                """,
                id=document_id,
                title=document.title,
                content=document.content,
            )

        document_data = result.single()
        return DocumentResponse(**document_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    language_id: str = None,
    db=Depends(get_db_dependency),
):
    """Upload a file for language documentation (simplified)"""
    try:
        # In a real implementation, you'd save to GCS and store the URL
        file_content = await file.read()

        document_id = str(uuid.uuid4())

        if language_id:
            result = db.run(
                """
                MATCH (l:Language {id: $language_id})
                CREATE (d:Document {
                    id: $id,
                    title: $title,
                    content: $content,
                    file_name: $file_name,
                    created_at: datetime()
                })
                CREATE (d)-[:DOCUMENTS]->(l)
                RETURN d.id as id, d.title as title
                """,
                id=document_id,
                title=f"Uploaded file: {file.filename}",
                content=f"File uploaded: {file.filename} ({len(file_content)} bytes)",
                file_name=file.filename,
                language_id=language_id,
            )
        else:
            result = db.run(
                """
                CREATE (d:Document {
                    id: $id,
                    title: $title,
                    content: $content,
                    file_name: $file_name,
                    created_at: datetime()
                })
                RETURN d.id as id, d.title as title
                """,
                id=document_id,
                title=f"Uploaded file: {file.filename}",
                content=f"File uploaded: {file.filename} ({len(file_content)} bytes)",
                file_name=file.filename,
            )

        document_data = result.single()
        return {
            "message": "File uploaded successfully",
            "document_id": document_data["id"],
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    language_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db_dependency),
):
    """Get list of documents"""
    try:
        if language_id:
            result = db.run(
                """
                MATCH (d:Document)-[:DOCUMENTS]->(l:Language {id: $language_id})
                RETURN d.id as id, d.title as title, d.content as content, 
                       l.id as language_id, toString(d.created_at) as created_at
                ORDER BY d.created_at DESC
                SKIP $skip LIMIT $limit
                """,
                language_id=language_id,
                skip=skip,
                limit=limit,
            )
        else:
            result = db.run(
                """
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:DOCUMENTS]->(l:Language)
                RETURN d.id as id, d.title as title, d.content as content, 
                       l.id as language_id, toString(d.created_at) as created_at
                ORDER BY d.created_at DESC
                SKIP $skip LIMIT $limit
                """,
                skip=skip,
                limit=limit,
            )

        documents = [DocumentResponse(**record) for record in result]
        return documents

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
