from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import unquote, urlparse

from src.config import load_project_config
from src.interfaces.web.templates import build_index_page
from src.serving.inference import load_dashboard_bundle, load_inference_bundle, predict_single
from src.utils.logger import configure_project_logging, get_logger

logger = get_logger('web-server')


def create_request_handler(config: Dict[str, Any], bundle: Dict[str, Any], dashboard: Dict[str, Any]) -> type[BaseHTTPRequestHandler]:
    artifact_root = Path(config['project_root']).resolve()

    class PredictionHandler(BaseHTTPRequestHandler):
        def send_json(self, payload: Dict[str, Any], status_code: int = 200) -> None:
            response_body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        def send_html(self, html_content: str) -> None:
            body = html_content.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

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

        def _resolve_artifact(self, raw_path: str) -> Path | None:
            relative_path = raw_path.removeprefix('/artifacts/')
            candidate = (artifact_root / unquote(relative_path)).resolve()
            try:
                candidate.relative_to(artifact_root)
            except ValueError:
                return None
            return candidate if candidate.is_file() else None

        def do_GET(self) -> None:  # noqa: N802
            parsed_path = urlparse(self.path)
            if parsed_path.path == '/':
                self.send_html(build_index_page())
                return
            if parsed_path.path == '/health':
                self.send_json({'success': True, 'message': 'service is running'})
                return
            if parsed_path.path == '/api/v1/dashboard':
                self.send_json({'success': True, 'data': dashboard})
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

        def do_POST(self) -> None:  # noqa: N802
            if self.path != '/api/v1/predict':
                logger.warning('未找到请求资源：path={} | client={}', self.path, self.address_string())
                self.send_json({'success': False, 'message': '未找到请求资源'}, status_code=404)
                return
            content_length = int(self.headers.get('Content-Length', '0'))
            request_body = self.rfile.read(content_length).decode('utf-8')
            try:
                logger.info('收到预测请求：path={} | client={}', self.path, self.address_string())
                payload = json.loads(request_body)
                result = predict_single(payload, config, bundle)
                self.send_json(result)
            except Exception as error:  # noqa: BLE001
                logger.exception('预测失败：path={} | client={}', self.path, self.address_string())
                self.send_json({'success': False, 'message': f'预测失败：{error}'}, status_code=400)

        def log_message(self, format_string: str, *args: Any) -> None:
            logger.info('{} - {}', self.address_string(), format_string % args)

    return PredictionHandler


def run_server(host: str = '127.0.0.1', port: int = 8000) -> None:
    config = load_project_config()
    configure_project_logging(config['project_root'], relative_log_path=config['output_dirs']['logs'] + '/project.log')
    bundle = load_inference_bundle(config)
    dashboard = load_dashboard_bundle(config)
    handler = create_request_handler(config, bundle, dashboard)
    server = ThreadingHTTPServer((host, port), handler)
    logger.info('Web 演示服务已启动：http://{}:{}', host, port)
    server.serve_forever()
