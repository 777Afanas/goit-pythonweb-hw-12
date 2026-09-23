import os
import sys
from dotenv import load_dotenv

# 1. Добавление корня проекта в sys.path
root_dir = os.path.abspath("../..")
sys.path.insert(0, root_dir)

# 2. Чтение переменных окружения
load_dotenv(os.path.join(root_dir, ".env"))

# Метаданные
project = "Contacts REST API"
copyright = "2026, FullStack Python"
author = "Yatsenko"
release = "1.0.0"

# Расширения
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "nature"
html_static_path = ["_static"]

# Отключение строгой проверки и подсказок типов для внешних модулей
nitpicky = False
autodoc_typehints = "none"

# Подавление предупреждений от внешних ссылок и docutils
suppress_warnings = [
    "ref.ref",
    "ref.doc",
    "ref.python",
    "autodoc.import_object",
    "docutils",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "imported-members": False,
}


def autodoc_skip_member(app, what, name, obj, skip, options):
    """
    Пропускает любые объекты, не определенные явно в текущем модуле проекта,
    а также любые внешние библиотеки (FastAPI, SQLAlchemy и т.д.).
    """
    mod = getattr(obj, "__module__", None)
    if not mod or not isinstance(mod, str):
        return skip

    # Игнорируем внешние пакеты
    if any(lib in mod for lib in ("fastapi", "sqlalchemy", "starlette", "pydantic")):
        return True

    # Игнорируем импорты из других файлов проекта
    current_module = options.get("module")
    if current_module and mod != current_module:
        return True

    return skip


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)
