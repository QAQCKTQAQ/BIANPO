# 使用 Python 3.8 基础镜像
FROM python:3.8

# 设置工作目录
WORKDIR /app

# 复制项目文件到工作目录
COPY . /app

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建挂载点
VOLUME ["/app/config", "/app/data_directory"]

# 执行你的应用程序
ENTRYPOINT ["python"]
CMD ["powersystem_client.py"]

