import asyncio
import os
import aiohttp
from functools import wraps
from spider import ua
headers = {'User-Agent': ua.random}
def async_retry(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

@async_retry(max_retries=3, delay=2)
async def download_single_image(session, goods_info, proxy, folder):
    async with session.get(goods_info['goods_image_url'], proxy=proxy) as response:
        if response.status == 200:
            content = await response.read()
            file_path = os.path.join(folder, goods_info['goods_image_name'])
            with open(file_path, 'wb') as f:
                f.write(content)
            return file_path
        else:
            raise Exception(f"Failed to download image. Status code: {response.status}")

async def download_pic_async(goods_info_list, proxy, folder='file'):
    os.makedirs(folder, exist_ok=True)
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = []
        for goods_info in goods_info_list:
            task = asyncio.create_task(download_single_image(session, goods_info, proxy, folder))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for goods_info, result in zip(goods_info_list, results):
            if isinstance(result, Exception):
                print(f"Error downloading image for {goods_info['goods_image_name']}: {str(result)}")
                goods_info['local_image_url'] = None
            else:
                goods_info['local_image_url'] = result

    return goods_info_list
