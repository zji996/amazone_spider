from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests
import json
import urllib3
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Boolean, Float, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.sql import select
from contextlib import asynccontextmanager
import re
import logging

# 忽略 HTTPS 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = "sqlite:///./test.db"  # 使用 SQLite 数据库；你可以替换为其他数据库
database = Database(DATABASE_URL)
metadata = MetaData()

from sqlalchemy import Table

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

# 定义 AmazonFilter 类
class AmazonFilter:
    def __init__(self, name: str, country: str, type: str, page_start: int, min_stars: int, max_stars: int, min_likes: int, max_likes: int):
        self.name = name
        self.country = country
        self.type = type
        self.page_start = page_start
        self.min_stars = min_stars
        self.max_stars = max_stars
        self.min_likes = min_likes
        self.max_likes = max_likes
    
    def find_key(self, key: str) -> str:
        base_url = f"https://www.amazon.{self.country}/s"
        query_params = {
            'k': key,
            'page': self.page_start,
            'rh': f'p_72:{self.min_stars}-{self.max_stars},p_85:{self.min_likes}-{self.max_likes}'
        }
        query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        return f"{base_url}?{query_string}"
    
    def find_asin(self, asin: str) -> str:
        return f"https://www.amazon.{self.country}/dp/{asin}"
    
    def find_custom_url(self, url: str) -> str:
        return url

# 定义请求体模型
class URLRequest(BaseModel):
    url: str
    start_page: Optional[int] = 1
    end_page: Optional[int] = 1

class FilterRequest(BaseModel):
    name: Optional[str] = ''
    country: Optional[str] = 'com'
    type: Optional[str] = ''
    page_start: Optional[int] = 1
    min_stars: Optional[int] = 0
    max_stars: Optional[int] = 5
    min_likes: Optional[int] = 0
    max_likes: Optional[int] = 0
    key: str

# 加载 cookies
def load_cookies(path: str) -> dict:
    with open(path, 'r') as f:
        cookies = json.load(f)
        return cookies

# 获取 HTML 内容
def get_html_content(url, page=1):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.33',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    cookies = load_cookies('cookies.json')
    
    # 添加页码参数到 URL
    if '?' in url:
        url += f'&page={page}'
    else:
        url += f'?page={page}'
    
    try:
        main_page = requests.get(url=url, headers=headers, cookies=cookies, verify=False)
        main_page.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to fetch the URL: {e}")
        raise HTTPException(status_code=503, detail="Failed to fetch the URL")
    
    return main_page.text

# 提取包含 data-asin 的 <div> 元素
def get_table(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    goods_info_list = soup.find_all('div', attrs={'data-asin': True})
    return goods_info_list

# 提取商品信息
def get_goods_info(goods_info):
    pattern = re.compile(r'^\d{1,3}(,\d{3})* ratings')
    try:
        goods_discount = goods_info.find('span', class_='a-size-base s-highlighted-text-padding aok-inline-block s-coupon-highlight-color')
        goods_discount = goods_discount.text if goods_discount else None
    except AttributeError:
        goods_discount = None
    
    try:
        goods_is_prime = bool(goods_info.find('span', class_='a-icon a-icon-prime a-icon-medium'))
    except AttributeError:
        goods_is_prime = False
    
    try:
        goods_name = goods_info.find('div',attrs={'data-cy':"title-recipe"})
        goods_name = goods_name.text if goods_name else None
    except AttributeError:
        goods_name = None
    
    try:
        goods_comment = goods_info.find_all('span', attrs={'aria-label':pattern})
        print(goods_comment)
        goods_comment = goods_comment[0].get('aria-label') if goods_comment else None
    except AttributeError:
        goods_comment = None
    
    try:
        goods_price = goods_info.find('span', class_='a-price').find('span', class_='a-offscreen').text
    except AttributeError:
        goods_price = None
    
    try:
        asin = goods_info.get('data-asin')
        goods_url = f'https://www.amazon.com/dp/{asin}' if asin else None
    except AttributeError:
        goods_url = None
    
    try:
        goods_stars = goods_info.find('span', class_='a-icon-alt')
        goods_stars = float(goods_stars.text[:3]) if goods_stars else None
    except (AttributeError, ValueError):
        goods_stars = None
    
    try:
        goods_image = goods_info.find('img', class_='s-image')
        goods_image = goods_image['src'] if goods_image else None
    except AttributeError:
        goods_image = None
    
    return {
        'name': goods_name,
        'price': goods_price,
        'url': goods_url,
        'discount': goods_discount,
        'comment': goods_comment,
        'is_prime': goods_is_prime,
        'goods_stars': goods_stars,
        'goods_image': goods_image
    }

# 创建 FastAPI 应用
app = FastAPI()

# 配置 CORS
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def insert_goods_info(goods_info_list):
    for goods_info in goods_info_list:
        query = select(goods.c.url).where(goods.c.url == goods_info['url'])
        existing_goods = await database.fetch_one(query)
        if existing_goods is None:
            insert_query = goods.insert().values(goods_info)
            await database.execute(insert_query)

@app.post("/generate_url/")
def generate_url(filter_request: FilterRequest):
    try:
        amazon_filter = AmazonFilter(
            name=filter_request.name,
            country=filter_request.country,
            type=filter_request.type,
            page_start=filter_request.page_start,
            min_stars=filter_request.min_stars,
            max_stars=filter_request.max_stars,
            min_likes=filter_request.min_likes,
            max_likes=filter_request.max_likes
        )
        search_url = amazon_filter.find_key(filter_request.key)
        return {"url": search_url}
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"TypeError: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

# 定义 POST 请求
@app.post("/get-table")
async def get_table_endpoint(request: URLRequest):
    try:
        goods_info_list = []
        for page in range(request.start_page, request.end_page + 1):
            html = get_html_content(request.url, page)
            table = get_table(html)
            if not table:
                raise HTTPException(status_code=404, detail=f"No table found on page {page}")
            
            # 提取每个商品的信息
            goods_info_list.extend([get_goods_info(goods_info) for goods_info in table])
        await insert_goods_info(goods_info_list)
        
        return {"goods": goods_info_list}
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"TypeError: {str(e)}")
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@app.get("/get-goods")
async def get_goods():
    query = goods.select()
    goods_info_list = await database.fetch_all(query)
    return {"goods": goods_info_list}

@app.get("/clear-goods")
async def clear_goods():
    query = goods.delete()  # 构建删除所有记录的 SQL 查询
    await database.execute(query)  # 执行 SQL 查询
    return {"status": "All goods cleared"}

@app.post("/delete-goods/{item_id}")
async def delete_goods(item_id: int):
    query = goods.delete().where(goods.c.id == item_id)  # 构建通过 id 删除条目的 SQL 查询
    result = await database.execute(query)  # 执行 SQL 查询
    if result:
        return {"status": f"Goods with id {item_id} deleted"}
    raise HTTPException(status_code=404, detail=f"Goods with id {item_id} not found")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
