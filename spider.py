class AmazonFilter:
    def __init__(self) -> None:
        self.name = ''
        self.country = ''
        self.type = ''
        self.page_start = 1
        self.min_stars = 0
        self.max_stars = 5
        self.min_likes = 0
        self.max_likes = 0
    
    def set_name(self, name):
        self.name = name
    
    def set_country(self, country):
        self.country = country
    
    def set_type(self, type):
        self.type = type
    
    def set_page_start(self, page_start):
        self.page_start = page_start
    
    def set_stars_range(self, min_stars, max_stars):
        self.min_stars = min_stars
        self.max_stars = max_stars
    
    def set_likes_range(self, min_likes, max_likes):
        self.min_likes = min_likes
        self.max_likes = max_likes
    
    def find_key(self, key):
        base_url = f"https://www.amazon.{self.country}/s"
        query_params = {
            'k': key,
            'page': self.page_start,
            'rh': f'p_72:{self.min_stars}-{self.max_stars},p_85:{self.min_likes}-{self.max_likes}'
        }
        query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
        return f"{base_url}?{query_string}"
    
    def find_asin(self, asin):
        base_url = f"https://www.amazon.{self.country}/dp/{asin}"
        return base_url
    
    def find_custom_url(self, url):
        return url

# 示例用法
amazon_filter = AmazonFilter()
amazon_filter.set_country('com')
amazon_filter.set_name('example')
amazon_filter.set_page_start(1)
amazon_filter.set_stars_range(4, 5)
amazon_filter.set_likes_range(50, 100)

search_url = amazon_filter.find_key('laptop')
print(search_url)  # 输出生成的搜索URL
