from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional
class FilterRequest(BaseModel):
    name: str = Field(..., description="Filter name")
    country: str = Field(..., description="Country code")
    type: str = Field(..., description="Filter type")
    page_start: int = Field(..., description="Starting page number")
    min_stars: int = Field(..., description="Minimum stars")
    max_stars: int = Field(..., description="Maximum stars")
    min_likes: int = Field(..., description="Minimum likes")
    max_likes: int = Field(..., description="Maximum likes")
    key: str = Field(..., description="Search key")

    class Config:
        schema_extra = {
            "example": {
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
        }

# 定义 AmazonFilter 类
class AmazonFilter:
    def __init__(self, name: Optional[str] = None, country: Optional[str] = None, 
                 type: Optional[str] = None, page_start: Optional[int] = None, 
                 min_stars: Optional[int] = None, max_stars: Optional[int] = None, 
                 min_likes: Optional[int] = None, max_likes: Optional[int] = None):
        self.name = name
        self.country = country or "com"  # 默认值
        self.type = type
        self.page_start = page_start or 1  # 默认值
        self.min_stars = min_stars or 1  # 默认值
        self.max_stars = max_stars or 5  # 默认值
        self.min_likes = min_likes or 0  # 默认值
        self.max_likes = max_likes or 100  # 默认值
    
    def find_key(self, key: Optional[str]) -> str:
        if not key:
            return ""
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


class FilterRequest(BaseModel):
    name: str = Field(..., description="Filter name")
    country: str = Field(..., description="Country code")
    type: str = Field(..., description="Filter type")
    page_start: int = Field(..., description="Starting page number")
    min_stars: int = Field(..., description="Minimum stars")
    max_stars: int = Field(..., description="Maximum stars")
    min_likes: int = Field(..., description="Minimum likes")
    max_likes: int = Field(..., description="Maximum likes")
    key: str = Field(..., description="Search key")

    class Config:
        schema_extra = {
            "example": {
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
        }
