import requests
from bs4 import BeautifulSoup
import urllib3
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 假设 AmazonFilter 类定义如下：
class AmazonFilter:
    def __init__(self):
        self.name = ''
        self.country = 'com'
        self.type = ''
        self.page_start = 1
        self.min_stars = 0
        self.max_stars = 5
        self.min_likes = 0
        self.max_likes = 0

    def set_country(self, country: str):
        self.country = country

    def set_name(self, name: str):
        self.name = name

    def set_page_start(self, page_start: int):
        self.page_start = page_start

    def set_stars_range(self, min_stars: int, max_stars: int):
        self.min_stars = min_stars
        self.max_stars = max_stars

    def set_likes_range(self, min_likes: int, max_likes: int):
        self.min_likes = min_likes
        self.max_likes = max_likes

    def find_key(self, key: str) -> str:
        # 模拟生成的搜索 URL
        return f"https://www.amazon.{self.country}/s?k={key}&min_stars={self.min_stars}&max_stars={self.max_stars}&min_likes={self.min_likes}&max_likes={self.max_likes}"

# 实例化 AmazonFilter 并设置参数
filter = AmazonFilter()
filter.set_country('com')
filter.set_name('example')
filter.set_page_start(1)
filter.set_stars_range(4, 5)
filter.set_likes_range(50, 100)
search_url = filter.find_key('laptop')
print(search_url)
def load_cookies(path):
    with open('cookies.json', 'r') as f:
        cookies = json.load(f)
        return cookies
def open_html_content(path):
    with open(path, 'r', encoding='utf-8') as f:
        html = f.read()
        return html

def get_html_content(url):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}
    cookies = load_cookies('cookies.json')
    main_page = requests.get(url=url, headers=headers,cookies=cookies,verify=False)
    print(main_page.status_code)
    with open('content.html', 'w', encoding='utf-8') as f:
        f.write(main_page.text)
    return main_page.text

def get_table(html):
    soup = BeautifulSoup(html, 'html.parser')
    goods_info_list = soup.find_all('div',attrs={'data-asin': True})
    return goods_info_list
def get_goods_info(goods_info):
    # 提取商品信息
    goods_discount = goods_info.find('span', class_='a-size-base s-highlighted-text-padding aok-inline-block s-coupon-highlight-color').text 
    try:
        goods_info.find('span', class_='a-icon a-icon-prime a-icon-medium')
        goods_is_prime = True
    except:
        goods_is_prime = False
    goods_name = goods_info.find('span', class_='a-size-medium a-color-base a-text-normal').text
    goods_comment = goods_info.find('span', class_='a-size-base s-underline-text').text
    goods_price =goods_info.find('span',class_='a-price-symbol') + goods_info.find('span', class_='a-price-whole').text + '.' + goods_info.find('span', class_='a-price-fraction').text
    goods_url = 'https://www.amazon.com' + goods_info.find('a', class_='a-link-normal a-text-normal')['href']
    goods_stars = goods_info.find('span', class_='a-icon-alt').text[:3]
    goods_image = goods_info.find('img', class_='s-image')['src']
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

def main():
    html = get_html_content(search_url)
    with open('content.html', 'w', encoding='utf-8') as f:
        f.write(html)
    table = get_table(html)
    if table:
        print("Table found!")
    else:
        print("No table found.")

if __name__ == "__main__":
    main()
