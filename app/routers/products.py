from fastapi import APIRouter, status, HTTPException
from sqlalchemy import select, insert, update, func
from app.models import products
from app.schemas.product_schemas import ProductReponseSchema, ProductCreateSchema, ProductPatchSchema
from app.database import get_connection
from typing import List
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix='/products', tags=['products'])

@router.get('/', status_code=status.HTTP_200_OK, response_model=List[ProductReponseSchema])
async def get_products():
    """Получение всех товаров"""
    stmt = select(products).order_by(products.c.id)
    async with get_connection() as conn:
        result = await conn.execute(stmt)
        return result.mappings().all()


@router.get('/above-average', status_code=status.HTTP_200_OK, response_model=List[ProductReponseSchema])
async def get_products_average():
    """Получение товаров чья цена дороже средней цены"""
    subq = select(func.avg(products.c.price)).scalar_subquery()
    stmt = select(products).where(products.c.price > subq).order_by(products.c.price.desc())

    async with get_connection() as conn:
        result = await conn.execute(stmt)   
        return result.mappings().all()


@router.get('/{id}', status_code=status.HTTP_200_OK, response_model=ProductReponseSchema)
async def get_products(id: int):
    """Получение товара по ID"""
    stmt = select(products).where(products.c.id == id)
    async with get_connection() as conn:
        result = await conn.execute(stmt)
        product = result.mappings().one_or_none()

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product ID({id} not found.")

        return product


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=ProductReponseSchema)
async def post_product(product: ProductCreateSchema):
    """Создания товара"""
    try:
        stmt = (insert(products)
                .values(name=product.name, price=product.price, stock=product.stock, category=product.category)
                .returning(products))
        
        check_stmt = select(products).where(products.c.name == product.name)
        async with get_connection() as conn:

            existing = await conn.execute(check_stmt)
            if existing.first():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with name '{product.name}' already exists")


            result = await conn.execute(stmt)
            row = result.fetchone()
            return row._asdict()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
            print(f"Ошибка при создании: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.put('/{id}', status_code=status.HTTP_200_OK, response_model=ProductReponseSchema)
async def put_product(new_product: ProductCreateSchema, id: int):
    """Изменения продукта"""
    query = select(products).where(products.c.id == id)

    async with get_connection() as conn:
        result_query = await conn.execute(query)
        product = result_query.mappings().one_or_none()

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Product ID({id}) not found.')

        stmt = (update(products)
                .values(name=new_product.name, price=new_product.price, stock=new_product.stock, category=new_product.category)
                .where(products.c.id==id)
                .returning(products))
        result = await conn.execute(stmt)
        return result.mappings().first()


@router.patch('/{id}', status_code=status.HTTP_200_OK, response_model=ProductReponseSchema)
async def patch_product(new_product: ProductPatchSchema, id: int):
    """Изменения параметра в товаре"""
    query = select(products).where(products.c.id == id)

    async with get_connection() as conn:
        result_query = await conn.execute(query)
        product = result_query.mappings().one_or_none()

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Product ID({id}) not found.')

        patch_info = new_product.model_dump(exclude_none=True)

        if not patch_info:
            raise HTTPException(status_code=400, detail="At least one field must be provided for update.")
        

        stmt = update(products).where(products.c.id == id).values(patch_info).returning(products)
        result = await conn.execute(stmt)
        return result.mappings().first()
