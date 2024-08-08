from sqlalchemy import create_engine, Column, String, Boolean, Float, Integer, MetaData
from databases import Database
from sqlalchemy import Float
from sqlalchemy import Table
DATABASE_URL = "sqlite:///./test.db"  # 使用 SQLite 数据库；你可以替换为其他数据库
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
    Column("goods_image", String, nullable=True),
)
# 创建数据库引擎
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)