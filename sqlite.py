from sqlalchemy import create_engine, Column, String, Boolean, Float, Integer, MetaData
from databases import Database
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.sql import select
import time
from sqlalchemy import Table

DATABASE_URL = "sqlite+aiosqlite:///./public1.db"
database = Database(DATABASE_URL)
metadata = MetaData()

goods = Table(
    "goods",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("price", String),
    Column("url", String, unique=True, index=True),
    Column("discount", String, nullable=True),
    Column("comment", String, nullable=True),
    Column("is_prime", Boolean, default=False),
    Column("goods_stars", Float, nullable=True),
    Column("goods_image_url", String, nullable=True),
    Column("goods_image_name", String, nullable=True),
    Column("local_image_url", String, nullable=True),
    Column("timestamp", Integer, default=lambda: int(time.time()), nullable=False),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("username", String, unique=True, index=True, nullable=False),
    Column("password", String, nullable=False),
    Column("timestamp", Integer, default=lambda: int(time.time()), nullable=False),
    Column("token", String, nullable=False),
    #Column("is_admin", Boolean, default=True , default=False),
)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def create_tables():
    async with engine.begin() as conn:
        # 检查每个表是否存在，如果不存在则创建
        for table in metadata.tables.values():
            # 检查表是否存在
            if not await conn.run_sync(table.exists):
                # 表不存在，创建表
                await conn.run_sync(metadata.create_all)
                print(f"Table {table.name} created.")
            else:
                print(f"Table {table.name} already exists.")

async def verify_user_by_token(session: AsyncSession, token: str):
    stmt = select(users).where(users.c.token == token)
    result = await session.execute(stmt)
    user = result.fetchone()
    
    if user and user.token == token:
        return user
    return False
