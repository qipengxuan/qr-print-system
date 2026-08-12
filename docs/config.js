/**
 * 前端配置文件
 *
 * 本地部署：无需修改，API 请求自动发往同源地址
 * GitHub Pages 部署：需要设置后端地址
 *
 * 通过 URL 参数指定后端:
 *   https://yourname.github.io/qr-print-system/?api=192.168.1.100:8000
 * 或在页面中点击"切换"按钮手动设置
 */

// 默认空字符串 = 同源（本地部署时前端和后端在同一服务器）
let API_BASE = '';

// 从 URL 参数读取 (?api=192.168.1.100:8000)
const params = new URLSearchParams(location.search);
const apiParam = params.get('api');
if (apiParam) {
    API_BASE = apiParam.startsWith('http') ? apiParam : 'http://' + apiParam;
    localStorage.setItem('print_api_base', API_BASE);
}

// 从 localStorage 读取（记住上次设置）
if (!API_BASE) {
    API_BASE = localStorage.getItem('print_api_base') || '';
}

// 检测是否在 GitHub Pages 上运行（需要设置后端地址）
const IS_GITHUB_PAGES = location.hostname.endsWith('github.io');

// 如果在 GitHub Pages 上且未设置后端地址，自动提示
if (IS_GITHUB_PAGES && !API_BASE) {
    const saved = localStorage.getItem('print_api_base');
    if (!saved) {
        // 延迟提示，等页面加载完成
        window.addEventListener('load', () => {
            setTimeout(() => {
                alert(
                    '检测到你在 GitHub Pages 上访问。\n\n' +
                    '本系统需要连接你局域网内的后端服务才能打印。\n\n' +
                    '请确保:\n' +
                    '1. 后端程序已在与打印机同网络的电脑上运行\n' +
                    '2. 手机与该电脑在同一网络\n' +
                    '3. 点击下方"切换"按钮，输入电脑IP:8000\n\n' +
                    '例如: 192.168.1.100:8000'
                );
            }, 500);
        });
    }
}

/**
 * 获取 API 完整 URL
 * @param {string} path - API 路径，如 '/api/upload'
 * @returns {string} 完整 URL
 */
function apiUrl(path) {
    return API_BASE + path;
}

/**
 * 检查后端连接是否可用
 * @returns {Promise<boolean>}
 */
async function checkBackend() {
    try {
        const res = await fetch(apiUrl('/api/health'), { method: 'GET' });
        return res.ok;
    } catch (e) {
        return false;
    }
}
