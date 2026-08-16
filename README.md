## Стек
- FastAPI + SQLAlchemy 2.0 Core (не ORM!)
- asyncpg + асинхронные запросы
- Pydantic v2
- PostgreSQL

## Особенности
- Чистый SQLAlchemy Core (Table, Column, select(), insert())
- Сложные SQL-запросы: JOIN, CTE, подзапросы, агрегации
- Bulk-операции
- Транзакции при создании заказов

## Запуск

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Убедись, что PostgreSQL запущен и .env настроен

# 3. Запуск приложения
uvicorn app.main:app --reload

# 4. Наполнение тестовыми данными
python -m app.seed