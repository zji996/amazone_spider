from pydantic import BaseModel
from typing import Optional 
from sqlalchemy import func
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum

# 定义请求体模型

class URLRequest(BaseModel):
    url: HttpUrl = Field(..., description="The URL to request")
    start_page: Optional[int] = Field(1, ge=1, description="The starting page number")
    end_page: Optional[int] = Field(1, ge=1, description="The ending page number")
    token: Optional[str] = Field('123', description="The token to use for authentication")

class DeleteData(BaseModel):
    token: Optional[str] = Field(None, description="The token to use for authentication")
    id_list: Optional[list[int]] = Field(None, description="The main SQL key list")

class FilterRequest(BaseModel):
    name: Optional[str] = Field(default='', max_length=20,description="Filter name")
    country: Optional[str] = Field(default='com', max_length=20,description="Country code")
    type: Optional[str] = Field(default="serach", max_length=20,description="Filter type")
    page_start: Optional[int] = Field(default=1, ge=1,description="Starting page number")
    min_stars: Optional[int] = Field(default=0, ge=0,description="Minimum stars")
    max_stars: Optional[int] = Field(default=30000, ge=1,description="Maximum stars")
    min_likes: Optional[int] = Field(default=0, ge=0,description="Minimum likes")
    max_likes: Optional[int] = Field(default=1000, ge=1,description="Maximum likes")
    key: Optional[str] = Field(default='', max_length=20,description="Search key")
    token: Optional[str] = Field(None, description="The token to use for authentication")

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
    token: Optional[str] = Field(None, description="The token to use for authentication")

class RegisterRequest(BaseModel):
    username: str = Field(..., max_length=20,description="username")
    password: str = Field(..., max_length=20,description="password")
    secret: Optional[str] = Field(None, max_length=20,description="secret")
    timestamp: Optional[int] = Field(None, max_length=20,description="timestamp")
    lifespan: Optional[int] = Field(None, ge=0,description="lifespan")
    token: Optional[str] = Field(None, description="The token to use for authentication")

class ClearRequest(BaseModel):
    token: Optional[str] = Field(None, description="The token to use for authentication")

class GetGoodsPicture(BaseModel):
    id: int = Field(None,description="The main key of goods")