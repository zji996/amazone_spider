# 使用 Python 3.12.4 官方镜像作为基础镜像
FROM python:3.12.4

# 设置工作目录
WORKDIR /app
# 将当前目录下的所有文件复制到容器的工作目录
COPY . /app

# 安装 pip 依赖
RUN pip install --no-cache-dir \
    aiofiles==24.1.0 \
    aiohappyeyeballs==2.3.5 \
    aiohttp==3.10.3 \
    aiosignal==1.3.1 \
    aiosqlite==0.20.0 \
    annotated-types==0.7.0 \
    anyio==4.4.0 \
    attrs==24.2.0 \
    beautifulsoup4==4.12.3 \
    bs4==0.0.2 \
    certifi==2024.7.4 \
    charset-normalizer==3.3.2 \
    click==8.1.7 \
    colorama==0.4.6 \
    databases==0.9.0 \
    fake-useragent==1.5.1 \
    fastapi==0.112.0 \
    frozenlist==1.4.1 \
    greenlet==3.0.3 \
    h11==0.14.0 \
    httptools==0.6.1 \
    idna==3.7 \
    multidict==6.0.5 \
    pydantic==2.8.2 \
    pydantic_core==2.20.1 \
    python-dotenv==1.0.1 \
    PyYAML==6.0.1 \
    requests==2.32.3 \
    setuptools==72.1.0 \
    sniffio==1.3.1 \
    soupsieve==2.5 \
    SQLAlchemy==2.0.32 \
    starlette==0.37.2 \
    tqdm==4.66.5 \
    typing_extensions==4.12.2 \
    urllib3==2.2.2 \
    uvicorn==0.30.5 \
    watchfiles==0.22.0 \
    websockets==12.0 \
    wheel==0.43.0 \
    yarl==1.9.4

# 暴露容器的 8000 端口
EXPOSE 8000

CMD ["/bin/bash"]
# 定义容器启动时执行的命令
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
