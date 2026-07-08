from __future__ import annotations

import json
import mimetypes
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import unquote, urlparse

from src.config import load_project_config
from src.interfaces.web.templates import build_index_page
from src.interfaces.shared.dashboard_schema import TRAINING_MODE_OPTIONS
from src.serving.inference import load_dashboard_bundle, load_inference_bundle, predict_single
from src.log import configure_project_logging, get_logger

logger = get_logger('web-server')


# 构建请求处理器
def create_request_handler(config: Dict[str, Any], bundle: Dict[str, Any]) -> type[BaseHTTPRequestHandler]:
    artifact_root = Path(config['project_root']).resolve()
    allowed_training_modes = {item['value'] for item in TRAINING_MODE_OPTIONS}

    # 后台启动训练命令
    def launch_training(mode: str) -> None:
        command = [sys.executable, str(Path(config['project_root']) / 'main.py'), mode]
        subprocess.Popen(command, cwd=config['project_root'])

    # 读取最新 dashboard
    def current_dashboard() -> Dict[str, Any]:
        return load_dashboard_bundle(config)

    class PredictionHandler(BaseHTTPRequestHandler):
        # 返回 JSON 响应
        def send_json(self, payload: Dict[str, Any], status_code: int = 200) -> None:
            response_body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        # 返回 HTML 响应
        def send_html(self, html_content: str) -> None:
            body = html_content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # 返回静态文件
        def send_file(self, file_path: Path) -> None:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            body = file_path.read_bytes()
            self.send_response(200)
            if (mime_type or '').startswith('text/') or mime_type in {'image/svg+xml', 'application/json'}:
                content_type = (mime_type or 'application/octet-stream') + '; charset=utf-8'
            else:
                content_type = mime_type or 'application/octet-stream'
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        # 解析产物路径
        def _resolve_artifact(self, raw_path: str) -> Path | None:
            relative_path = raw_path.removeprefix('/artifacts/')
            candidate = (artifact_root / unquote(relative_path)).resolve()
            try:
                candidate.relative_to(artifact_root)
            except ValueError:
                return None
            return candidate if candidate.is_file() else None

        # 处理 GET 请求
        def do_GET(self) -> None:  # noqa: N802
            parsed_path = urlparse(self.path)
            if parsed_path.path == '/':
                self.send_html(build_index_page(current_dashboard()))
                return
            if parsed_path.path == '/health':
                self.send_json({'success': True, 'message': 'service is running'})
                return
            if parsed_path.path == '/api/v1/dashboard':
                self.send_json({'success': True, 'data': current_dashboard()})
                return
            if parsed_path.path.startswith('/artifacts/'):
                artifact_path = self._resolve_artifact(parsed_path.path)
                if artifact_path is None:
                    logger.warning('未找到请求资源：path={} | client={}', parsed_path.path, self.address_string())
                    self.send_json({'success': False, 'message': '未找到请求资源'}, status_code=404)
                    return
                self.send_file(artifact_path)
                return
            logger.warning('未找到请求资源：path={} | client={}', parsed_path.path, self.address_string())
            self.send_json({'success': False, 'message': '未找到请求资源'}, status_code=404)

        # 处理 POST 请求
        def do_POST(self) -> None:  # noqa: N802
            if self.path not in {'/api/v1/predict', '/api/v1/train'}:
                logger.warning('未找到请求资源：path={} | client={}', self.path, self.address_string())
                self.send_json({'success': False, 'message': '未找到请求资源'}, status_code=404)
                return
            content_length = int(self.headers.get('Content-Length', '0'))
            request_body = self.rfile.read(content_length).decode('utf-8')
            try:
                payload = json.loads(request_body or '{}')
                if self.path == '/api/v1/train':
                    mode = str(payload.get('training_mode', 'train'))
                    if mode not in allowed_training_modes:
                        self.send_json({'success': False, 'message': f'不支持的训练路线：{mode}'}, status_code=400)
                        return
                    if mode == 'artifacts-only':
                        self.send_json({'success': True, 'message': '仅展示已有产物，不启动训练。'})
                        return
                    logger.info('收到训练请求：mode={} | client={}', mode, self.address_string())
                    threading.Thread(target=launch_training, args=(mode,), daemon=True).start()
                    self.send_json({'success': True, 'message': f'已启动训练进程：python main.py {mode}'})
                    return
                logger.info('收到预测请求：path={} | client={}', self.path, self.address_string())
                result = predict_single(payload, config, bundle)
                self.send_json(result)
            except Exception as error:  # noqa: BLE001
                logger.exception('请求处理失败：path={} | client={}', self.path, self.address_string())
                self.send_json({'success': False, 'message': f'处理失败：{error}'}, status_code=400)

        # 统一访问日志格式
        def log_message(self, format_string: str, *args: Any) -> None:
            logger.info('{} - {}', self.address_string(), format_string % args)

    return PredictionHandler


# 启动 Web 服务
def run_server(host: str = '127.0.0.1', port: int = 8000) -> None:
    config = load_project_config()
    configure_project_logging(config['project_root'], relative_log_path=config['output_dirs']['logs'] + '/project.log')
    bundle = load_inference_bundle(config)
    handler = create_request_handler(config, bundle)
    server = ThreadingHTTPServer((host, port), handler)
    logger.info('Web 演示服务已启动：http://{}:{}', host, port)
    server.serve_forever()
