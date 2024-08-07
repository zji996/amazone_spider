from fastapi import FastAPI, HTTPException, Query,Body, Request
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests
import json
import urllib3
from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Boolean, Float, Integer, MetaData, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.sql import select
from contextlib import asynccontextmanager
import re
from fake_useragent import UserAgent
from sqlalchemy import cast, Float
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional
from pydantic import ValidationError
from enum import Enum
ua = UserAgent()
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
class AmazonFilter():
    def __init__(self, name: str, country: str, type: str, page_start: int, min_stars: int, max_stars: int, min_likes: int, max_likes: int, key: str):
        self.name = name
        self.country = country
        self.type = type
        self.page_start = page_start
        self.min_stars = min_stars
        self.max_stars = max_stars
        self.min_likes = min_likes
        self.max_likes = max_likes
        self.key = key
    
    def find_key(self: str) -> str:
        base_url = f"https://www.amazon.{self.country}/s"
        query_params = {
            'k': self.key,
            'page': self.page_start,
            'rh': f'p_72:{self.min_stars}-{self.max_stars},p_85:{self.min_likes}-{self.max_likes}'
        }
        query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        print(f"{base_url}?{query_string}")
        return f"{base_url}?{query_string}"
    
    def find_asin(self, asin: str) -> str:
        return f"https://www.amazon.{self.country}/dp/{asin}"
    
    def find_custom_url(self, url: str) -> str:
        return url

# 定义请求体模型

class URLRequest(BaseModel):
    url: HttpUrl = Field(..., description="The URL to request")
    start_page: Optional[int] = Field(1, ge=1, description="The starting page number")
    end_page: Optional[int] = Field(1, ge=1, description="The ending page number")

    @field_validator('end_page')
    def end_page_must_be_greater_or_equal_to_start_page(cls, v, info):
        if 'start_page' in info.data and v < info.data['start_page']:
            raise ValueError('end_page must be greater than or equal to start_page')
        return v

    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.amazon.com/s?k=laptop&crid=E4IFH65CN7W3&sprefix=laptop%2Caps%2C316&ref=nb_sb_noss_1",
                "start_page": 1,
                "end_page": 5
            }
        }
class deleteData(BaseModel):
    id: int = Field(...,ge=1,description="the main sql key")

class FilterRequest(BaseModel):
    name: Optional[str] = Field(default='', max_length=20,description="Filter name")
    country: Optional[str] = Field(default='.com', max_length=20,description="Country code")
    type: Optional[str] = Field(default="serach", max_length=20,description="Filter type")
    page_start: Optional[int] = Field(default=1, ge=1,description="Starting page number")
    min_stars: Optional[int] = Field(default=0, ge=0,description="Minimum stars")
    max_stars: Optional[int] = Field(default=30000, ge=1,description="Maximum stars")
    min_likes: Optional[int] = Field(default=0, ge=0,description="Minimum likes")
    max_likes: Optional[int] = Field(default=1000, ge=1,description="Maximum likes")
    key: Optional[str] = Field(default='', max_length=20,description="Search key")

    # class Config:
    #     schema_extra = {
    #         "example": {
    #             "name": "Example Filter",
    #             "country": "com",
    #             "type": "search",
    #             "page_start": 1,
    #             "min_stars": 1,
    #             "max_stars": 5,
    #             "min_likes": 0,
    #             "max_likes": 100,
    #             "key": "laptop"
    #         }
    #     }

# 获取 HTML 内容
def get_html_content(url, page=1):
    headers = {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    # 添加页码参数到 URL
    if '?' in url:
        url += f'&page={page}'
    else:
        url += f'?page={page}'
    
    main_page = requests.get(url=url, headers=headers, verify=False)
    if main_page.status_code != 200:
        HTTPException(status_code=main_page.status_code, detail="Failed to fetch the URL")
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
    
    if goods_name is None:
        return None
    
    try:
        goods_comment = goods_info.find_all('span', attrs={'aria-label':pattern})
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
    # "http://localhost.tiangolo.com",
    # "https://localhost.tiangolo.com",
    # "http://localhost",
    # "http://localhost:8000",

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


@app.post("/generateUrl/")
def generate_url(filter_request : FilterRequest = Body(
    ...,
    example = {
                "name": "Example Filter",
                "country": "com",
                "type": "search",
                "page_start": 1,
                "min_stars": 1,
                "max_stars": 5,
                "min_likes": 0,
                "max_likes": 100,
                "key": "laptop"
            }
                                                     )):
    try:
        amazon_filter = AmazonFilter(
            name=filter_request.name,
            country=filter_request.country,
            type=filter_request.type,
            page_start=filter_request.page_start,
            min_stars=filter_request.min_stars,
            max_stars=filter_request.max_stars,
            min_likes=filter_request.min_likes,
            max_likes=filter_request.max_likes,
            key = filter_request.key
        )
        search_url = amazon_filter.find_key()
        return {"url": search_url}
    # except TypeError as e:
    #      HTTPException(status_code=400, detail=f"TypeError: {str(e)}")
    # except Exception as e:
    #      HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
    except Exception as e:
    # 捕获所有类型的异常，并返回状态码为 400 的 HTTP 异常
        raise HTTPException(status_code=400, detail="请求无法处理，请检查输入")
# 定义 POST 请求
@app.post("/getTable")
async def get_table_endpoint(
    request: URLRequest = Body(
        ...,
        example={
            "url": "https://www.amazon.com/s?k=laptop&crid=E4IFH65CN7W3&sprefix=laptop%2Caps%2C316&ref=nb_sb_noss_1",
            "start_page": 1,
            "end_page": 5
        }
    )
):
    try:
        goods_info_list = []
        # 将 HttpUrl 对象转换为字符串
        url = str(request.url)
        for page in range(request.start_page, request.end_page + 1):
            try:
                html = get_html_content(url, page)
                table = get_table(html)
                if not table:
                    continue
                
                # 提取每个商品的信息，并跳过名称为 None 的商品
                for goods_info in table:
                    goods_data = get_goods_info(goods_info)
                    if goods_data and goods_data['name']:
                        goods_info_list.append(goods_data)
            except Exception as e:
                # 记录错误但继续处理下一页
                print(f"Error processing page {page}: {str(e)}")
                continue
                    
        if goods_info_list:
            await insert_goods_info(goods_info_list)
            return {"goods": goods_info_list}
        else:
            raise HTTPException(status_code=404, detail="未找到商品信息")

    except ValidationError as e:
        # 处理请求体验证错误
        error_messages = []
        for error in e.errors():
            error_messages.append(f"Field: {error['loc'][0]}, Error: {error['msg']}")
        raise HTTPException(status_code=422, detail=error_messages)

    except HTTPException as he:
        # 重新抛出 HTTP 异常
        raise he

    except Exception as e:
        # 捕获所有其他类型的异常，并返回状态码为 500 的 HTTP 异常
        print(f"Unexpected error: {str(e)}")  # 记录错误以便调试
        raise HTTPException(status_code=500, detail="服务器内部错误")

# @app.get("/getGoods")
# async def get_goods():
#     query = goods.select()
#     goods_info_list = await database.fetch_all(query)
#     return {"goods": goods_info_list}

@app.middleware("http")
async def log_request(request: Request, call_next):
    # 打印请求头
    print("Headers:")
    for key, value in request.headers.items():
        print(f"{key}: {value}")

    # 打印请求体
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        print("Body:")
        try:
            print(json.dumps(json.loads(body.decode("utf-8")), indent=4))
        except json.JSONDecodeError:
            print(body.decode("utf-8"))

    response = await call_next(request)
    return response

@app.get("/clearGoods")
async def clear_goods():
    query = goods.delete()  # 构建删除所有记录的 SQL 查询
    await database.execute(query)  # 执行 SQL 查询
    return {"status": "All goods cleared"}


@app.post("/deleteGoods/")
async def delete_goods(request: deleteData = Body(
        ...,
        example={
            "id": 1
        }
    )):
    try:
        query = goods.delete().where(goods.c.id == request.id)  # 构建通过 id 删除条目的 SQL 查询
        result = await database.execute(query)  # 执行 SQL 查询
        if result:
            return {"status": f"Goods with id {request.id} deleted"}
        # HTTPException(status_code=404, detail=f"Goods with id {item_id} not found")
    except Exception as e:
    # 捕获所有类型的异常，并返回状态码为 400 的 HTTP 异常
        raise HTTPException(status_code=400, detail="请求无法处理，请检查输入")

class SortField(str, Enum):
    price = "price"
    likes = "likes"
    stars = "stars"
    # 添加其他可能的排序字段

class SortRequest(BaseModel):
    sort_by: SortField = SortField.price
    page: int = 1
    per_page: int = 8
    ascending: bool = True

@app.post("/sortGoods")
async def sort_goods(
    request: SortRequest = Body(
        ...,
        example={
            "sort_by": "price",
            "page": 1,
            "per_page": 8,
            "ascending": True
        }
    )
    ):
    try:
        offset = (request.page - 1) * request.per_page
        # 验证排序字段是否存在
        if request.sort_by.value not in goods.c:
            raise ValueError(f"Invalid sort field: {request.sort_by}")
        try:
            query = select(func.count()).select_from(goods)
            result = await database.fetch_val(query)
        except Exception as e:
            print(f"Error: {str(e)}")
            raise HTTPException(status_code=500, detail="无法获取商品总数")
        order_by = cast(goods.c[request.sort_by.value], Float).asc() if request.ascending else cast(goods.c[request.sort_by.value], Float).desc()
        query = goods.select().order_by(order_by).offset(offset).limit(request.per_page)
        goods_info_list = await database.fetch_all(query)
        
        # 将 Record 对象转换为字典
        goods_info_list = [dict(record) for record in goods_info_list]
        
        return {"goods": goods_info_list,"len":result}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # 捕获所有其他类型的异常，并返回状态码为 400 的 HTTP 异常
        print(f"Unexpected error: {str(e)}")  # 记录错误以便调试
        raise HTTPException(status_code=400, detail="请求无法处理，请检查输入")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
