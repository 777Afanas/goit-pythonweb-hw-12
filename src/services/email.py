from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD, # type: ignore
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_verification_email(email: str, username: str, host: str, token: str):
    verification_link = f"{host}api/auth/confirmed_email/{token}"
    body = (
        f"Привіт, {username}!\nБудь ласка, підтвердіть реєстрацію: {verification_link}"
    )
    message = MessageSchema(
        subject="Email Verification",
        recipients=[email],  # type: ignore
        body=body,
        subtype=MessageType.plain,
    )
    fm = FastMail(conf)
    await fm.send_message(message)
