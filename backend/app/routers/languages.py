from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from app.database import get_db_dependency
import uuid

router = APIRouter()


# Pydantic models for languages
class LanguageCreate(BaseModel):
    name: str
    iso_code: str = None
    description: str = None


class LanguageResponse(BaseModel):
    id: str
    name: str
    iso_code: str = None
    description: str = None
    created_at: str


@router.post("/", response_model=LanguageResponse)
async def create_language(
    language: LanguageCreate,
    db=Depends(get_db_dependency),
):
    """Create a new language entry"""
    try:
        language_id = str(uuid.uuid4())
        result = db.run(
            """
            CREATE (l:Language {
                id: $id,
                name: $name,
                iso_code: $iso_code,
                description: $description,
                created_at: datetime()
            })
            RETURN l.id as id, l.name as name, l.iso_code as iso_code, 
                   l.description as description, toString(l.created_at) as created_at
            """,
            id=language_id,
            name=language.name,
            iso_code=language.iso_code,
            description=language.description,
        )

        language_data = result.single()
        return LanguageResponse(**language_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[LanguageResponse])
async def get_languages(skip: int = 0, limit: int = 100, db=Depends(get_db_dependency)):
    """Get list of languages"""
    try:
        result = db.run(
            """
            MATCH (l:Language)
            RETURN l.id as id, l.name as name, l.iso_code as iso_code, 
                   l.description as description, toString(l.created_at) as created_at
            ORDER BY l.created_at DESC
            SKIP $skip LIMIT $limit
            """,
            skip=skip,
            limit=limit,
        )

        languages = [LanguageResponse(**record) for record in result]
        return languages

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{language_id}", response_model=LanguageResponse)
async def get_language(language_id: str, db=Depends(get_db_dependency)):
    """Get specific language by ID"""
    try:
        result = db.run(
            """
            MATCH (l:Language {id: $id})
            RETURN l.id as id, l.name as name, l.iso_code as iso_code, 
                   l.description as description, toString(l.created_at) as created_at
            """,
            id=language_id,
        )

        language_data = result.single()
        if not language_data:
            raise HTTPException(status_code=404, detail="Language not found")

        return LanguageResponse(**language_data)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
