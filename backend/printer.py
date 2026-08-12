"""
打印机通信模块
支持柯美 bizhub 287，通过 RAW/Port 9100 发送 PDF 直接打印
备用方案：CUPS lp 命令
"""
import socket
import subprocess
from pathlib import Path


class PrinterService:
    """柯美 bizhub 287 打印机通信服务"""

    def __init__(self, ip: str, port: int = 9100):
        self.ip = ip
        self.port = port
        self.timeout = 30

    def check_connection(self) -> bool:
        """检查打印机端口是否可达"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.ip, self.port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def print_pdf(self, pdf_path: str, job_name: str = "Print Job") -> tuple:
        """
        通过 RAW/Port 9100 发送 PDF 到打印机
        bizhub 287 支持 PDF v1.7 直接打印

        Returns: (success: bool, message: str)
        """
        path = Path(pdf_path)
        if not path.exists():
            return (False, f"文件不存在: {pdf_path}")

        file_size = path.stat().st_size
        if file_size == 0:
            return (False, "文件为空")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, self.port))

            # 分块发送 PDF 文件
            with open(pdf_path, "rb") as f:
                while True:
                    chunk = f.read(65536)  # 64KB
                    if not chunk:
                        break
                    sock.sendall(chunk)

            sock.close()
            return (True, f"已发送 {file_size / 1024:.1f} KB 至 {self.ip}:{self.port}")

        except ConnectionRefusedError:
            return (False, f"打印机拒绝连接 {self.ip}:{self.port}，请检查打印机是否开机")
        except socket.timeout:
            return (False, "连接打印机超时，请检查网络")
        except OSError as e:
            return (False, f"打印异常: {e}")

    def print_via_cups(self, pdf_path: str, printer_name: str = "bizhub287") -> tuple:
        """
        通过 CUPS lp 命令打印（备用方案）
        需先在系统中添加打印机: lpadmin -p bizhub287 -E -v socket://10.1.13.252:9100 -m everywhere
        """
        try:
            result = subprocess.run(
                ["lp", "-d", printer_name, pdf_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return (True, f"CUPS 任务已提交: {result.stdout.strip()}")
            return (False, f"CUPS 打印失败: {result.stderr}")
        except FileNotFoundError:
            return (False, "CUPS 未安装")
        except subprocess.TimeoutExpired:
            return (False, "CUPS 打印超时")
