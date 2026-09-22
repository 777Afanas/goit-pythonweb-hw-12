"""Модуль маршрутизації для автентифікації та керування доступом користувачів.

Включає реєстрацію, підтвердження електронної пошти, вхід з видачею пари токенів
(access/refresh), ротацію токенів та механізм скидання пароля.
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Security,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository.users import UserRepository
from src.schemas import (
    RequestResetPassword,
    ResetPassword,
    TokenModel,
    UserCreate,
    UserResponse,
)
from src.services.auth import AuthService
from src.services.email import send_reset_password_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """Реєструє нового користувача та відправляє лист для підтвердження email.

    :param body: Дані нового користувача (username, email, password).
    :param background_tasks: Менеджер фонових завдань FastAPI.
    :param request: Об'єкт HTTP-запиту для отримання базового URL.
    :param db: Сесія бази даних SQLAlchemy.
    :raises HTTPException: 409 Conflict, якщо email вже зайнятий.
    :return: Створений об'єкт користувача.
    """
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


@router.post("/login", response_model=TokenModel)
def login(
    body: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Автентифікує користувача та видає пару токенів (access і refresh).

    :param body: Форма авторизації (username містить email, password).
    :param db: Сесія бази даних SQLAlchemy.
    :raises HTTPException: 401 Unauthorized, якщо дані невірні або email не підтверджено.
    :return: Словник з access_token, refresh_token та token_type.
    """
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
    refresh_token = AuthService.create_refresh_token({"sub": user.email})

    # Оновлення refresh токена в БД через шар репозиторію
    user_repo.update_token(user, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/confirmed_email/{token}")
def confirmed_email(token: str, db: Session = Depends(get_db)):
    """Підтверджує адресу електронної пошти за email-токеном.

    :param token: JWT токен верифікації зі scope 'email_token'.
    :param db: Сесія бази даних SQLAlchemy.
    :raises HTTPException: 400 Bad Request, якщо токен недійсний або користувача не знайдено.
    :return: Повідомлення про успішне підтвердження.
    """
    email = AuthService.decode_token(token, expected_scope="email_token")

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


@router.get("/refresh_token", response_model=TokenModel)
def refresh_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db),
):
    """Виконує безпечну ротацію пари токенів за допомогою refresh token.

    :param credentials: Заголовок авторизації Bearer із refresh токеном.
    :param db: Сесія бази даних SQLAlchemy.
    :raises HTTPException: 401 Unauthorized, якщо токен недійсний, відкликаний або застарілий.
    :return: Нова пара access_token та refresh_token.
    """
    token = credentials.credentials
    email = AuthService.decode_token(token, expected_scope="refresh_token")

    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(email)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Захист від повторного використання: звірка зі збереженим значенням
    if user.refresh_token != token:
        user_repo.update_token(user, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )

    new_access_token = AuthService.create_access_token({"sub": user.email})
    new_refresh_token = AuthService.create_refresh_token({"sub": user.email})

    user_repo.update_token(user, new_refresh_token)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/request_reset_password")
def request_reset_password(
    body: RequestResetPassword,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """Ініціює процедуру відновлення пароля та надсилає лист із посиланням.

    :param body: Схема з email адресою облікового запису.
    :param background_tasks: Менеджер фонових завдань FastAPI.
    :param request: Об'єкт HTTP-запиту.
    :param db: Сесія бази даних SQLAlchemy.
    :return: Інформаційне повідомлення про відправку інструкцій.
    """
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(body.email)
    if user:
        reset_token = AuthService.create_email_token({"sub": user.email})
        background_tasks.add_task(
            send_reset_password_email,
            user.email,
            user.username,
            str(request.base_url),
            reset_token,
        )
    return {"message": "Check your email for the reset instructions"}


@router.post("/reset_password")
def reset_password(
    body: ResetPassword,
    db: Session = Depends(get_db),
):
    """Встановлює новий пароль користувача після перевірки валідності токена.

    :param body: Схема із захисним токеном скидання та новим паролем.
    :param db: Сесія бази даних SQLAlchemy.
    :raises HTTPException: 400 Bad Request, якщо токен недійсний або користувача не знайдено.
    :return: Повідомлення про успішну зміну пароля.
    """
    email = AuthService.decode_token(body.token, expected_scope="email_token")

    user_repo = UserRepository(db)
    user = user_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    new_hashed_password = AuthService.get_password_hash(body.new_password)
    user_repo.update_password(user, new_hashed_password)
    return {"message": "Password successfully updated"}
