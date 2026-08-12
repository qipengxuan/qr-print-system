"""
扫码自助打印系统 - 后端服务
支持柯美 bizhub 287 打印机 (RAW / Port 9100)
前端可部署在 GitHub Pages，通过 CORS 跨域访问后端 API
"""
import os
import io
import time
import uuid
import base64
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import qrcode

from printer import PrinterService
from file_converter import convert_to_pdf

# ==================== 配置 ====================
PRINTER_IP = os.environ.get("PRINTER_IP", "10.1.13.252")
PRINTER_PORT = int(os.environ.get("PRINTER_PORT", "9100"))
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", "./storage"))
STORAGE_DIR.mkdir(exist_ok=True)
JOB_EXPIRE_SECONDS = 1800  # 30 分钟过期

# 前端目录：支持本地开发和 Docker 两种路径
# 默认指向 docs/ 目录（兼容 GitHub Pages 部署）
FRONTEND_DIR = Path(os.environ.get(
    "FRONTEND_DIR",
    str(Path(__file__).parent.parent / "docs")
))

# ==================== 作业存储 ====================
jobs: dict = {}  # {token: job_info}
printer = PrinterService(PRINTER_IP, PRINTER_PORT)


async def cleanup_expired_jobs():
    """定期清理过期作业及文件"""
    while True:
        await asyncio.sleep(60)
        now = time.time()
        expired = [t for t, j in jobs.items() if now > j["expires_at"]]
        for token in expired:
            job = jobs.pop(token)
            for key in ("file_path", "pdf_path"):
                p = Path(job.get(key, ""))
                if p.exists():
                    try:
                        p.unlink()
                    except OSError:
                        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(cleanup_expired_jobs())
    yield


# ==================== 初始化 ====================
app = FastAPI(title="扫码自助打印系统", version="1.1.0", lifespan=lifespan)

# CORS：允许 GitHub Pages 和任何前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态资源（如果前端目录存在）
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ==================== 页面路由 ====================

@app.get("/")
async def index():
    """手机上传页面"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/kiosk")
async def kiosk():
    """扫码终端页面"""
    return FileResponse(str(FRONTEND_DIR / "kiosk.html"))


# ==================== API 路由 ====================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件 -> 生成取件码 + 二维码"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过 50MB 限制")

    job_id = uuid.uuid4().hex
    token = uuid.uuid4().hex[:6].upper()

    # 保存原始文件
    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    original_path = STORAGE_DIR / f"{job_id}_{safe_name}"
    original_path.write_bytes(content)

    # 转换为 PDF
    try:
        pdf_path = convert_to_pdf(original_path, STORAGE_DIR, job_id)
    except Exception as e:
        original_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))

    # 存储作业
    jobs[token] = {
        "job_id": job_id,
        "filename": file.filename,
        "file_path": str(original_path),
        "pdf_path": str(pdf_path),
        "status": "pending",
        "created_at": time.time(),
        "expires_at": time.time() + JOB_EXPIRE_SECONDS,
    }

    # 生成二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "success": True,
        "token": token,
        "filename": file.filename,
        "qr_code": f"data:image/png;base64,{qr_b64}",
        "expires_in": JOB_EXPIRE_SECONDS,
    }


@app.post("/api/print/{token}")
async def print_job(token: str):
    """根据取件码触发打印"""
    token = token.upper().strip()

    if token not in jobs:
        raise HTTPException(status_code=404, detail="取件码无效或已过期")

    job = jobs[token]

    if time.time() > job["expires_at"]:
        jobs.pop(token, None)
        raise HTTPException(status_code=410, detail="取件码已过期，请重新上传文件")

    if job["status"] == "printing":
        return {"status": "printing", "message": "正在打印中，请稍候..."}

    if job["status"] == "printed":
        return {"status": "printed", "message": "该文件已打印完成"}

    job["status"] = "printing"

    try:
        success, message = printer.print_pdf(
            job["pdf_path"], job_name=job["filename"]
        )

        if success:
            job["status"] = "printed"
            job["printed_at"] = time.time()

            async def delayed_cleanup():
                await asyncio.sleep(60)
                for key in ("file_path", "pdf_path"):
                    p = Path(job.get(key, ""))
                    if p.exists():
                        p.unlink(missing_ok=True)

            asyncio.create_task(delayed_cleanup())
            return {"status": "success", "message": message, "filename": job["filename"]}

        job["status"] = "error"
        return JSONResponse(
            status_code=502,
            content={"status": "error", "message": message},
        )

    except Exception as e:
        job["status"] = "error"
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"打印异常: {e}"},
        )


@app.get("/api/status/{token}")
async def job_status(token: str):
    """查询作业状态"""
    token = token.upper().strip()
    if token not in jobs:
        raise HTTPException(status_code=404, detail="取件码无效或已过期")

    job = jobs[token]
    remaining = int(job["expires_at"] - time.time())

    return {
        "token": token,
        "filename": job["filename"],
        "status": job["status"],
        "remaining_seconds": max(0, remaining),
    }


@app.get("/api/health")
async def health():
    """健康检查 + 打印机连通性"""
    reachable = printer.check_connection()
    return {
        "status": "ok",
        "printer_ip": PRINTER_IP,
        "printer_port": PRINTER_PORT,
        "printer_reachable": reachable,
        "active_jobs": len(jobs),
    }


if __name__ == "__main__":
    import uvicorn

    print(f"\n{'=' * 50}")
    print(f"  扫码自助打印系统 v1.1")
    print(f"  打印机: {PRINTER_IP}:{PRINTER_PORT}")
    print(f"  手机上传: http://<本机IP>:8000/")
    print(f"  扫码终端: http://<本机IP>:8000/kiosk")
    print(f"  健康检查: http://<本机IP>:8000/api/health")
    print(f"{'=' * 50}\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
