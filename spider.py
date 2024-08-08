from fastapi import HTTPException
from bs4 import BeautifulSoup
import requests
import re
from fake_useragent import UserAgent
ua = UserAgent()
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