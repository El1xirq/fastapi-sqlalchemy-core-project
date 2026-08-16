import asyncio
import random
from decimal import Decimal
from sqlalchemy import insert, text
from app.database import get_connection
from app.models import users, products, orders, order_item


async def clear_tables(conn):
    """Очистка всех таблиц с сбросом автоинкремента."""
    await conn.execute(text("""
        TRUNCATE TABLE users, products, orders, order_items 
        RESTART IDENTITY CASCADE
    """))


async def seed_users(conn):
    """Заполнение пользователей."""
    data = [
        {"name": "Алексей", "email": "alex@example.com", "age": 28},
        {"name": "Мария", "email": "maria@example.com", "age": 24},
        {"name": "Иван", "email": "ivan@example.com", "age": 35},
        {"name": "Ольга", "email": "olga@example.com", "age": 30},
        {"name": "Дмитрий", "email": "dmitry@example.com", "age": 42},
        {"name": "Анна", "email": "anna@example.com", "age": 27},
        {"name": "Сергей", "email": "sergey@example.com", "age": 31},
    ]
    stmt = insert(users).values(data).returning(users.c.id)
    result = await conn.execute(stmt)
    return [row.id for row in result.fetchall()]


async def seed_products(conn):
    """Заполнение товаров. Возвращает словарь {id: price}."""
    data = [
        {"name": "Ноутбук ASUS VivoBook", "price": 75000.00, "stock": 15, "category": "Электроника"},
        {"name": "Мышь Logitech MX", "price": 2500.00, "stock": 50, "category": "Электроника"},
        {"name": "Клавиатура Keychron K3", "price": 8000.00, "stock": 30, "category": "Электроника"},
        {"name": "Кофе зерновой Brazil 1кг", "price": 1200.00, "stock": 100, "category": "Продукты"},
        {"name": "Блокнот Moleskine A5", "price": 350.00, "stock": 200, "category": "Канцелярия"},
        {"name": "Наушники Sony WH-1000", "price": 15000.00, "stock": 20, "category": "Электроника"},
        {"name": "Монитор LG 27\"", "price": 32000.00, "stock": 10, "category": "Электроника"},
        {"name": "Чай зелёный Sencha 100г", "price": 450.00, "stock": 80, "category": "Продукты"},
    ]
    stmt = insert(products).values(data).returning(products.c.id, products.c.price)
    result = await conn.execute(stmt)
    return {row.id: Decimal(str(row.price)) for row in result.fetchall()}


async def seed_orders_and_items(conn, user_ids, product_map):
    """Создание заказов и позиций к ним."""
    product_ids = list(product_map.keys())
    
    # Генерируем 10 заказов
    for _ in range(10):
        user_id = random.choice(user_ids)
        num_items = random.randint(1, 4)
        selected_products = random.sample(product_ids, num_items)
        
        # Считаем total и собираем items
        total = Decimal("0")
        items = []
        for pid in selected_products:
            qty = random.randint(1, 5)
            price = product_map[pid]
            total += price * qty
            items.append({
                "product_id": pid,
                "quantity": qty,
                "price_at_time": float(price)
            })
        
        # Вставляем заказ
        stmt = insert(orders).values(
            user_id=user_id,
            total=float(total.quantize(Decimal("0.01")))
        ).returning(orders.c.id)
        result = await conn.execute(stmt)
        order_id = result.fetchone().id
        
        # Вставляем позиции заказа
        for item in items:
            item["order_id"] = order_id
            await conn.execute(insert(order_item).values(item))


async def seed():
    """Главная функция заполнения БД."""
    async with get_connection() as conn:
        await clear_tables(conn)
        user_ids = await seed_users(conn)
        product_map = await seed_products(conn)
        await seed_orders_and_items(conn, user_ids, product_map)
        print("✅ Seed completed successfully!")
        print(f"   Users: {len(user_ids)}")
        print(f"   Products: {len(product_map)}")
        print(f"   Orders: 10")


if __name__ == "__main__":
    asyncio.run(seed())