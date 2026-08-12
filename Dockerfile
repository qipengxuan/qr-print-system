FROM python:3.10-slim

# 安装 LibreOffice（Office 文档转 PDF）和基础依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-impress \
    libreoffice-calc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖文件，利用 Docker 缓存
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ .

# 复制前端文件
COPY frontend/ /app/frontend

# 创建存储目录
RUN mkdir -p /app/storage

ENV FRONTEND_DIR=/app/frontend
ENV STORAGE_DIR=/app/storage
ENV PRINTER_IP=10.1.13.252
ENV PRINTER_PORT=9100

EXPOSE 8000

CMD ["python", "main.py"]
