import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.repository.users import UserRepository
from src.schemas import Token, UserCreate, UserResponse
from src.services.auth import AuthService
from src.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    user_repo = UserRepository(db)
    exist_user = user_repo.get_user_by_email(body.email)
    if exist_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    hashed_password = AuthService.get_password_hash(body.password)
    user = user_repo.create_user(body, hashed_password)
    email_token = AuthService.create_email_token({"sub": user.email})
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.username,
        str(request.base_url),
        email_token,
    )
    return user


@router.post("/login", response_model=Token)
def login(
    body: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(body.username)
    if not user or not AuthService.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified",
        )

    access_token = AuthService.create_access_token({"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
def confirmed_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification error",
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )

    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )
    if user.confirmed:
        return {"message": "Email already confirmed"}

    user_repo.confirm_email(email)
    return {"message": "Email successfully confirmed"}
