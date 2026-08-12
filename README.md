# 扫码自助打印系统

支持柯美 bizhub 287 打印机，用户手机上传文件后扫码自助打印。

## 部署方式

### 方式一：Docker 一键部署（推荐）

```bash
git clone https://github.com/qipengxuan/qr-print-system.git
cd qr-print-system

# 修改打印机 IP（如果不同）
# 编辑 docker-compose.yml 中的 PRINTER_IP

# 启动
docker-compose up -d
```

### 方式二：本地运行

```bash
git clone https://github.com/qipengxuan/qr-print-system.git
cd qr-print-system/backend
pip install -r requirements.txt
python main.py
```

### 方式三：前端部署到 GitHub Pages + 后端本地运行

1. 进入仓库 Settings > Pages，Source 选择 `main` 分支，目录选 `/docs`
2. 等待部署完成，获得 GitHub Pages 地址（如 `https://qipengxuan.github.io/qr-print-system/`）
3. 在打印机同网络的电脑上运行后端：
   ```bash
   git clone https://github.com/qipengxuan/qr-print-system.git
   cd qr-print-system
   docker-compose up -d
   ```
4. 手机访问 GitHub Pages 地址，首次打开时设置后端地址为 `http://你的电脑IP:8000`

## 访问地址

| 页面 | 地址 |
|------|------|
| 手机上传 | `http://<服务器IP>:8000/` |
| 扫码终端 | `http://<服务器IP>:8000/kiosk` |
| 健康检查 | `http://<服务器IP>:8000/api/health` |

## 配置

通过环境变量或 `docker-compose.yml` 配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PRINTER_IP` | 10.1.13.252 | 打印机 IP |
| `PRINTER_PORT` | 9100 | 打印机端口 |
| `STORAGE_DIR` | ./storage | 文件存储目录 |

## 使用流程

1. 用户手机访问上传页面，选择文件上传
2. 系统自动转换为 PDF，生成 6 位取件码和二维码
3. 用户前往打印机旁的扫码终端
4. 扫码枪扫描二维码（或手动输入取件码）
5. 系统通过 Port 9100 将 PDF 发送到 bizhub 287
6. 打印完成后自动删除文件

## 支持的文件格式

- PDF (直接打印)
- 图片: PNG / JPG / GIF / BMP / TIFF / WEBP
- Office: DOC / DOCX / PPT / PPTX / XLS / XLSX (需 LibreOffice，Docker 镜像已内置)

## 网络要求

**后端服务必须运行在与打印机相同的局域网内**，因为打印机 IP 是内网地址，云端无法直接访问。

手机访问上传页面时，需要与后端服务器网络可达（同一 WiFi 或局域网）。

## 文件结构

```
qr-print-system/
├── docs/                 # 前端（可部署到 GitHub Pages）
│   ├── index.html         # 手机上传页面
│   ├── kiosk.html         # 扫码终端页面
│   └── config.js          # API 地址配置
├── backend/               # 后端
│   ├── main.py            # FastAPI 主应用
│   ├── printer.py         # 打印机通信 (Port 9100)
│   ├── file_converter.py  # 文件转 PDF
│   └── requirements.txt   # Python 依赖
├── Dockerfile             # Docker 镜像构建
├── docker-compose.yml     # Docker Compose 编排
├── .env.example           # 环境变量示例
└── README.md
```

## 扫码终端部署

扫码终端需要一台 PC 或迷你主机，连接 USB 扫码枪，用浏览器全屏打开 kiosk 页面。

USB 扫码枪会被系统识别为键盘设备，扫描二维码后自动输入取件码并按回车键触发打印。
