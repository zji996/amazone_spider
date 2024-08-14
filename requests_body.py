from pydantic import BaseModel,field_validator
from typing import Optional 
from sqlalchemy import func
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum

# 定义请求体模型

class CreateTask(BaseModel):
    url: Optional[str] = Field(..., description="The URL to request")
    start_page: Optional[int] = Field(1, ge=1, description="The starting page number")
    end_page: Optional[int] = Field(1, ge=1, description="The ending page number")

class DeleteData(BaseModel):
    id_list: Optional[list[int]] = Field(None, description="The main SQL key list")


class FilterRequest(BaseModel):
    name: Optional[str] = Field(default='', max_length=20,description="Filter name")
    country: Optional[str] = Field(default='com',description="Country code")
    type: Optional[str] = Field(default="serach", max_length=20,description="Filter type")
    page_start: Optional[int] = Field(default=1, ge=1,description="Starting page number")
    min_stars: Optional[int] = Field(default=0, ge=0,description="Minimum stars")
    max_stars: Optional[int] = Field(default=30000, ge=1,description="Maximum stars")
    min_likes: Optional[int] = Field(default=0, ge=0,description="Minimum likes")
    max_likes: Optional[int] = Field(default=1000, ge=1,description="Maximum likes")
    key: Optional[str] = Field(default='', max_length=20,description="Search key")
    @field_validator('country')
    def validate_country(cls, v):
        allowed_countries = [
            'com',      # 美国
            'co.uk',    # 英国
            'de',       # 德国
            'fr',       # 法国
            'it',       # 意大利
            'es',       # 西班牙
            'ca',       # 加拿大
            'jp',       # 日本
            'in',       # 印度
            'com.mx',   # 墨西哥
            'com.br',   # 巴西
            'com.au',   # 澳大利亚
            'nl',       # 荷兰
            'sg',       # 新加坡
            'ae',       # 阿拉伯联合酋长国
            'sa',       # 沙特阿拉伯
            'se',       # 瑞典
            'pl',       # 波兰
            'com.tr',   # 土耳其
            'cn',       # 中国（注意：亚马逊中国已停止运营，但保留域名）
            'co.jp',    # 日本（替代域名）
            'com.mx',   # 墨西哥
            'com.sg',   # 新加坡（替代域名）
            'com.ae',   # 阿联酋（替代域名）
        ]
        if v not in allowed_countries:
            raise ValueError
        return v

class GetToken(BaseModel):
    username: Optional[str] = Field(default='', max_length=20,description="username")
    password: Optional[str] = Field(default='', max_length=20,description="password")
    secret: Optional[str] = Field(default='', max_length=20,description="secret")
    timestamp: Optional[int] = Field(default=0, max_length=20,description="timestamp")
    lifespan: Optional[int] = Field(default=0, ge=0,description="lifespan")
class SortField(str, Enum):
    price = "price"
    likes = "likes"
    stars = "stars"

class SortRequest(BaseModel):
    sort_by: SortField = Field(default=SortField.price,description="The field to sort by")
    page: int = Field(1, ge=1,description="The page number to return")
    per_page: int = Field(10, ge=1,description="The number of items to return per page")
    ascending: bool = Field(default=True,description="Whether to sort in ascending order")

class RegisterRequest(BaseModel):
    username: str = Field(..., max_length=20,description="username")
    password: str = Field(..., max_length=20,description="password")
    secret: Optional[str] = Field(None, max_length=20,description="secret")
    timestamp: Optional[int] = Field(None, max_length=20,description="timestamp")
    lifespan: Optional[int] = Field(None, ge=0,description="lifespan")
