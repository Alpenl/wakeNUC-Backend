# 构建阶段
FROM python:3.10-slim AS builder

# 将 requirements.txt 复制到容器中
COPY requirements.txt /requirements.txt

# 使用阿里云镜像源安装依赖
RUN pip install --user -r /requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# 运行阶段
FROM python:3.10-slim

# 从构建阶段复制安装的依赖
COPY --from=builder /root/.local /root/.local

# 将应用代码复制到容器中
COPY . /app

# 设置环境变量，确保可以找到安装的依赖
ENV PATH=/root/.local/bin:$PATH

# 设置工作目录
WORKDIR /app

# 正确设置时区为上海
RUN apt-get update && apt-get install -y tzdata \
    && ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 定义容器启动时运行的命令
CMD ["python", "index.py"]