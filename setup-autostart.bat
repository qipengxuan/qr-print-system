@echo off
chcp 65001 >nul 2>&1

:: ============================================
:: 设置开机自启 - 将启动脚本加入启动文件夹
:: ============================================

echo 正在设置开机自启...

:: 获取启动文件夹路径
set STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

:: 创建快捷方式（用 PowerShell 生成 .lnk）
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut('%STARTUP_DIR%\扫码打印系统.lnk'); $sc.TargetPath = 'E:\qr-print-system-main\start.bat'; $sc.WorkingDirectory = 'E:\qr-print-system-main'; $sc.WindowStyle = 7; $sc.Description = '扫码自助打印系统开机自启'; $sc.Save()"

if exist "%STARTUP_DIR%\扫码打印系统.lnk" (
    echo.
    echo 设置成功！
    echo 快捷方式位置: %STARTUP_DIR%\扫码打印系统.lnk
    echo.
    echo 开机后会自动在后台启动打印系统。
    echo 如需取消自启，删除该快捷方式即可。
) else (
    echo 设置失败，请手动将 start.bat 的快捷方式复制到:
    echo %STARTUP_DIR%
)

echo.
pause
