"""
打印机通信模块
支持柯美 bizhub 287，通过 RAW/Port 9100 发送 PDF 直接打印
支持双面打印（长边/短边翻转）和纸张尺寸（A3/A4/A5）
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

    def _build_pjl_header(self, job_name: str, duplex: str = "simplex",
                          paper_size: str = "A4") -> bytes:
        """
        构建 PJL 命令头
        duplex: "simplex" | "longedge" | "shortedge"
        paper_size: "A3" | "A4" | "A5"
        """
        UEL = b"\x1b%-12345X"

        header = UEL
        header += b"@PJL\r\n"
        header += f'@PJL JOB NAME="{job_name}"\r\n'.encode("ascii", "replace")

        # 双面打印设置
        if duplex == "longedge":
            header += b"@PJL SET DUPLEX=ON\r\n"
            header += b"@PJL SET BINDING=LONGEDGE\r\n"
        elif duplex == "shortedge":
            header += b"@PJL SET DUPLEX=ON\r\n"
            header += b"@PJL SET BINDING=SHORTEDGE\r\n"
        else:
            header += b"@PJL SET DUPLEX=OFF\r\n"

        # 纸张尺寸
        if paper_size in ("A3", "A4", "A5"):
            header += f"@PJL SET PAPER={paper_size}\r\n".encode()

        # 份数
        header += b"@PJL SET COPIES=1\r\n"

        return header

    def _build_pjl_footer(self) -> bytes:
        """构建 PJL 命令尾"""
        UEL = b"\x1b%-12345X"
        footer = UEL
        footer += b"@PJL\r\n"
        footer += b"@PJL EOJ\r\n"
        footer += UEL
        return footer

    def print_pdf(self, pdf_path: str, job_name: str = "Print Job",
                  duplex: str = "simplex", paper_size: str = "A4") -> tuple:
        """
        通过 RAW/Port 9100 发送 PDF 到打印机
        bizhub 287 支持 PDF v1.7 直接打印
        使用 PJL 命令控制双面打印和纸张尺寸

        duplex: "simplex"(单面) | "longedge"(长边翻转) | "shortedge"(短边翻转)
        paper_size: "A3" | "A4" | "A5"

        Returns: (success: bool, message: str)
        """
        path = Path(pdf_path)
        if not path.exists():
            return (False, f"文件不存在: {pdf_path}")

        file_size = path.stat().st_size
        if file_size == 0:
            return (False, "文件为空")

        # 构建 PJL 命令
        pjl_header = self._build_pjl_header(job_name, duplex, paper_size)
        pjl_footer = self._build_pjl_footer()

        duplex_desc = {
            "simplex": "单面",
            "longedge": "双面(长边翻转)",
            "shortedge": "双面(短边翻转)"
        }.get(duplex, "单面")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, self.port))

            # 先发送 PJL 头
            sock.sendall(pjl_header)

            # 发送 PDF 文件内容
            with open(pdf_path, "rb") as f:
                while True:
                    chunk = f.read(65536)  # 64KB
                    if not chunk:
                        break
                    sock.sendall(chunk)

            # 发送 PJL 尾
            sock.sendall(pjl_footer)

            sock.close()
            return (True, f"已发送 {file_size / 1024:.1f} KB 至 {self.ip}:{self.port} "
                    f"({duplex_desc}, {paper_size})")

        except ConnectionRefusedError:
            return (False, f"打印机拒绝连接 {self.ip}:{self.port}，请检查打印机是否开机")
        except socket.timeout:
            return (False, "连接打印机超时，请检查网络")
        except OSError as e:
            return (False, f"打印异常: {e}")

    def print_via_cups(self, pdf_path: str, printer_name: str = "bizhub287",
                       duplex: str = "simplex", paper_size: str = "A4") -> tuple:
        """
        通过 CUPS lp 命令打印（备用方案）
        需先在系统中添加打印机: lpadmin -p bizhub287 -E -v socket://10.1.13.252:9100 -m everywhere
        """
        options = []

        # 双面打印
        if duplex == "longedge":
            options.extend(["-o", "sides=two-sided-long-edge"])
        elif duplex == "shortedge":
            options.extend(["-o", "sides=two-sided-short-edge"])
        else:
            options.extend(["-o", "sides=one-sided"])

        # 纸张尺寸
        if paper_size in ("A3", "A4", "A5"):
            options.extend(["-o", f"media={paper_size}"])

        try:
            result = subprocess.run(
                ["lp", "-d", printer_name] + options + [pdf_path],
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
