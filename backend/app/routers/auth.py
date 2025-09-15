from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.database import get_db_dependency
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic models for auth
class UserCreate(BaseModel):
    email: str
    password: str
    name: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


@router.post("/register", response_model=Token)
async def register(user: UserCreate, db=Depends(get_db_dependency)):
    """Register a new user"""
    try:
        # Check if user exists
        result = db.run("MATCH (u:User {email: $email}) RETURN u", email=user.email)
        if result.single():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        hashed_password = pwd_context.hash(user.password)
        result = db.run(
            """
            CREATE (u:User {
                email: $email,
                name: $name,
                password: $password,
                created_at: datetime()
            })
            RETURN u.email as email, u.name as name
            """,
            email=user.email,
            name=user.name,
            password=hashed_password,
        )

        user_data = result.single()
        access_token = create_access_token(data={"sub": user_data["email"]})
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(user: UserLogin, db=Depends(get_db_dependency)):
    """Login user and return access token"""
    try:
        # Get user
        result = db.run(
            "MATCH (u:User {email: $email}) RETURN u.email as email, u.password as password, u.name as name",
            email=user.email,
        )
        user_data = result.single()

        if not user_data or not pwd_context.verify(
            user.password, user_data["password"]
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = create_access_token(data={"sub": user_data["email"]})
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me")
async def get_current_user(db=Depends(get_db_dependency)):
    """Get current user information (simplified for demo)"""
    # In a real app, you'd decode the JWT token and get the actual user
    result = db.run("MATCH (u:User) RETURN u.email as email, u.name as name LIMIT 1")
    user_data = result.single()
    if user_data:
        return {"email": user_data["email"], "name": user_data["name"]}
    else:
        return {"message": "No users found"}
