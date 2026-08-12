/**
 * 前端配置文件
 *
 * 本地部署：无需修改，API 请求自动发往同源地址
 * GitHub Pages 部署：将 API_BASE 改为你的后端地址，例如:
 *   const API_BASE = 'http://192.168.1.100:8000';
 *
 * 也可以通过 URL 参数临时指定:
 *   https://yourname.github.io/qr-print-system/?api=192.168.1.100:8000
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

/**
 * 获取 API 完整 URL
 * @param {string} path - API 路径，如 '/api/upload'
 * @returns {string} 完整 URL
 */
function apiUrl(path) {
    return API_BASE + path;
}

/**
 * 获取当前配置的后端地址
 * @returns {string}
 */
function getApiBase() {
    return API_BASE || location.origin;
}
