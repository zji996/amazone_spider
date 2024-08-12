from fastapi import FastAPI, HTTPException, Query,Body, Request,status
from fastapi.responses import FileResponse
import json
import urllib3
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.sql import select
from sqlalchemy import cast, Float
from pydantic import ValidationError
import os
from requests_body import *
from sqlite import *
from spider import *
import hashlib
from tqdm import tqdm
# 忽略 HTTPS 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        # 在这里创建表
        await conn.run_sync(metadata.create_all)
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     await database.connect()
#     # 在数据库连接后创建表
#     await create_tables()
#     yield
#     await database.disconnect()

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

async def is_image_url_exist(session, image_name):
    stmt = select(goods).where(goods.c.goods_image_name == image_name)
    result = await session.execute(stmt)
    return result.scalar() is not None

@app.post("/getTable")
async def get_table_endpoint(
    request: URLRequest = Body(
        ...,
        example={
            "url": "https://www.amazon.com/s?k=laptop&crid=E4IFH65CN7W3&sprefix=laptop%2Caps%2C316&ref=nb_sb_noss_1",
            "start_page": 1,
            "end_page": 5,
            "token": "123"
        }
    )
):
    try:
        async with async_session() as session:
            async with session.begin():
                user = await verify_user_by_token(session, request.token)
            
                if user:
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
                            for goods_info in tqdm(table):
                                goods_data = get_goods_info(goods_info)
                                if goods_data and goods_data['name'] and goods_data['goods_image_url']:
                                    # 检查数据库中是否已存在相同的图片URL
                                    if not await is_image_url_exist(session, goods_data['goods_image_name']):
                                        download_pic_sync(goods_data['goods_image_url'])  # 同步下载图片
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
                else:
                    raise HTTPException(status_code=401,detail='token错误')
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

@app.post("/clearGoods")
async def clear_goods(request: ClearRequest = Body(...)):
    async with async_session() as session:
        async with session.begin():
            user = await verify_user_by_token(session, request.token)
            
            if user:
                # 如果用户验证通过，执行删除操作
                await session.execute(goods.delete())
                return {"status": "All goods cleared"}
            if not user:
                raise HTTPException(status_code=401,detail='token错误')
            else:
                raise HTTPException(status_code=404, detail="User not found or token mismatch")


@app.post("/deleteGoods/")
async def delete_goods(request: DeleteData = Body(..., example={"token": "123", "id_list": [1, 2, 3]})):
    try:
        async with async_session() as session:
            async with session.begin():
                user = await verify_user_by_token(session, request.token)
                
                if user:
                    # 检查每个ID是否存在，然后尝试删除
                    deleted_ids = []
                    not_found_ids = []
                    for item_id in request.id_list:
                        query = goods.delete().where(goods.c.id == item_id)
                        result = await session.execute(query)
                        if result.rowcount > 0:
                            deleted_ids.append(item_id)
                        else:
                            not_found_ids.append(item_id)
                    await session.commit()
                    
                    if not_found_ids:
                        raise HTTPException(status_code=404, detail=f"Goods with IDs {not_found_ids} not found")
                    return {"status": f"Goods with IDs {deleted_ids} successfully deleted"}
                if not user:
                    raise HTTPException(status_code=401,detail='token错误')
                else:
                    raise HTTPException(status_code=404, detail="User not found or token mismatch")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/sortGoods")
async def sort_goods(
    request: SortRequest = Body(
        ...,
        example={
            "sort_by": "price",
            "page": 1,
            "per_page": 8,
            "ascending": True,
            "token": "123"
        }
    )
    ):
    async with async_session() as session:
        async with session.begin():
            user = await verify_user_by_token(session, request.token)
            if user == False:
                raise HTTPException(status_code=401,detail='token错误')
            if user:
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
    # except Exception as e:
    #     # 捕获所有其他类型的异常，并返回状态码为 400 的 HTTP 异常
    #     print(f"Unexpected error: {str(e)}")  # 记录错误以便调试
    #     raise HTTPException(status_code=400, detail="请求无法处理，请检查输入")

# def encrypt_password(username: str, password: str) -> str:
#     current_time = str(int(time.time()))
#     data = f"{username}{password}{current_time}"
#     sha256 = hashlib.sha256()
#     sha256.update(data.encode('utf-8'))
#     return sha256.hexdigest()
def load_image(file_name):
    try:
        with open(f'./file/{file_name}','rb') as f:
            return f.read()
    except:
        Exception

@app.get("/getGoodsPicture/{file_name}")
async def get_picture(file_name: str):
    goods_image = file_name
    image_path = f"./file/{goods_image}"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found on server")

    media_type = determine_media_type(goods_image)  # 确保你有逻辑来确定文件的MIME类型
    return FileResponse(image_path, media_type=media_type)

def determine_media_type(filename: str) -> str:
    """根据文件扩展名确定媒体类型"""
    EXTENSION_TO_MEDIA_TYPE = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".png": "image/png"
    }
    ext = os.path.splitext(filename)[1].lower()
    return EXTENSION_TO_MEDIA_TYPE.get(ext, "application/octet-stream")
                
@app.post("/getToken")
async def get_token(request: GetToken = Body(...)):
    async with async_session() as session:
        async with session.begin():
            # 从数据库异步查询用户
            stmt = select(users).where(users.c.username == request.username)
            result = await session.execute(stmt)
            user = result.fetchone()
            
            if user:
                if user.password == encrypt_password(request.password+'123'+request.username):
                    token = user.token
                    return {"token": token}
                else:
                    raise HTTPException(status_code=400, detail="Incorrect password")
            else:
                raise HTTPException(status_code=404, detail="Username not found")

def encrypt_password(password: str) -> str:
    # 创建一个新的 sha256 hash 对象
    sha_signature = hashlib.sha256(password.encode()).hexdigest()
    return sha_signature

@app.post("/register")
async def register_user(request: RegisterRequest = Body(...)):
    async with async_session() as session:
        async with session.begin():
            # 异步检查用户名是否已存在
            stmt = select(users).where(users.c.username == request.username)
            result = await session.execute(stmt)
            user = result.scalar()
            
            if user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
            
            # 加密密码
            encrypted_password = encrypt_password(request.password+'123'+request.username)
            
            # 异步创建新用户
            new_user = users.insert().values(
                username=request.username,
                password=encrypted_password,
                token=encrypted_password  # 示例 token，实际应用中需要生成
            )
            await session.execute(new_user)
            # session.commit() 在 async with session.begin() 中自动处理

            return {"status": "User registered successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
