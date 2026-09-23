"""
Модуль для взаємодії з хмарним сервісом Cloudinary.

Забезпечує завантаження та трансформацію файлів аватарів користувачів.
"""

import cloudinary
import cloudinary.uploader
from src.conf.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_avatar(file, public_id: str) -> str:
    """Завантажує файл зображення на Cloudinary та повертає оптимізований URL.

    :param file: Файловий об'єкт для завантаження.
    :param public_id: Унікальний публічний ідентифікатор файлу в Cloudinary.
    :return: Сформований URL зображення з фіксованими розмірами 250x250.
    """
    result = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True)
    return cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=result.get("version")
    )
