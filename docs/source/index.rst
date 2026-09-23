Документація Contacts REST API
==============================

REST API застосунок для керування контактами, побудований на базі FastAPI, SQLAlchemy, PostgreSQL та Redis.

.. toctree::
   :maxdepth: 2
   :caption: Зміст проекту:

Точка входу (Main)
------------------
.. automodule:: main
   :members:

Модулі маршрутів (API)
----------------------
.. automodule:: src.api.contacts
   :members:

.. automodule:: src.api.auth
   :members:

.. automodule:: src.api.users
   :members:

Репозиторії (Repository)
------------------------
.. automodule:: src.repository.contacts
   :members:

.. automodule:: src.repository.users
   :members:

Сервіси (Services)
------------------
.. automodule:: src.services.contacts
   :members:

.. automodule:: src.services.auth
   :members:

.. automodule:: src.services.email
   :members:

.. automodule:: src.services.upload_avatar
   :members:

.. automodule:: src.services.roles
   :members:

База даних та кеш (Database & Cache)
------------------------------------
.. automodule:: src.database.models
   :members:
   :no-value:

.. automodule:: src.database.cache
   :members: