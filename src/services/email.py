"""
Модуль для роботи з поштовим сервісом за допомогою бібліотеки FastAPI-Mail.

Забезпечує формування конфігурації підключення та відправку транзакційних листів:
підтвердження реєстрації акаунта та запиту на скидання пароля.
"""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,  # type: ignore
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
)


async def send_verification_email(
    email: EmailStr, username: str, host: str, token: str
) -> None:
    """Відправляє лист користувачу для підтвердження адреси електронної пошти.

    :param email: Адреса електронної пошти отримувача.
    :param username: Ім'я користувача для персоналізації повідомлення.
    :param host: Базовий URL хоста застосунку.
    :param token: JWT токен верифікації пошти.
    """
    verification_link = f"{host}api/auth/confirmed_email/{token}"
    html_content = f"""
    <html>
        <body>
            <p>Привіт, <strong>{username}</strong>!</p>
            <p>Дякуємо за реєстрацію. Будь ласка, підтвердіть вашу електронну пошту, перейшовши за посиланням нижче:</p>
            <p><a href="{verification_link}">Підтвердити електронну пошту</a></p>
            <br>
            <p>Якщо ви не реєструвалися в системі, проігноруйте цей лист.</p>
        </body>
    </html>
    """
    try:
        message = MessageSchema(
            subject="Email Verification",
            recipients=[email],  # type: ignore
            body=html_content,
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except ConnectionErrors as err:
        print(f"Помилка відправки email верифікації: {err}")


async def send_reset_password_email(
    email: EmailStr, username: str, host: str, token: str
) -> None:
    """Відправляє лист з інструкцією та токеном для скидання забутого пароля.

    :param email: Адреса електронної пошти користувача.
    :param username: Ім'я користувача.
    :param host: Базовий URL хоста застосунку.
    :param token: Тимчасовий JWT токен для скидання пароля.
    """
    html_content = f"""
    <html>
        <body>
            <p>Привіт, <strong>{username}</strong>!</p>
            <p>Ви надіслали запит на скидання пароля для вашого облікового запису.</p>
            <p>Ваш одноразовий токен для скидання пароля:</p>
            <p><code>{token}</code></p>
            <br>
            <p>Використайте цей токен у запиті до ендпоінту <code>/api/auth/reset_password</code> разом із новим паролем.</p>
            <p>Якщо ви не надсилали цей запит, проігноруйте це повідомлення.</p>
        </body>
    </html>
    """
    try:
        message = MessageSchema(
            subject="Password Reset Request",
            recipients=[email],  # type: ignore
            body=html_content,
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except ConnectionErrors as err:
        print(f"Помилка відправки email для скидання пароля: {err}")
