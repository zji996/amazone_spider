from pydantic import BaseModel
from typing import Optional 
from sqlalchemy import func
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional
from enum import Enum

# 定义请求体模型

class URLRequest(BaseModel):
    url: HttpUrl = Field(..., description="The URL to request")
    start_page: Optional[int] = Field(1, ge=1, description="The starting page number")
    end_page: Optional[int] = Field(1, ge=1, description="The ending page number")
    token: Optional[str] = Field('123', description="The token to use for authentication")
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
    token: Optional[str] = Field(None, description="The token to use for authentication")

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

class getToken(BaseModel):
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
    pass