@echo off
chcp 65001 >nul 2>&1
title 扫码自助打印系统

:: ============================================
:: 扫码自助打印系统 - 启动脚本
:: ============================================

:: 切换到项目目录
cd /d E:\qr-print-system-main\backend

:: 打印机配置（如需修改，改这里）
set PRINTER_IP=10.1.13.252
set PRINTER_PORT=9100
set PORT=9000

:: 检查 Python 是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请确保已安装 Python 并添加到 PATH
    pause
    exit /b 1
)

:: 检查依赖是否已安装
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [提示] 首次运行，正在安装依赖...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请手动运行: python -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)

:: 启动服务
echo.
echo ==========================================
echo   扫码自助打印系统已启动
echo   打印机: %PRINTER_IP%:%PRINTER_PORT%
echo   手机上传: http://本机IP:%PORT%/
echo   扫码终端: http://本机IP:%PORT%/kiosk
echo ==========================================
echo.

python main.py

:: 如果程序异常退出，暂停以便查看错误
pause
