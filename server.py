"""
音声文字起こしツールのWeb版サーバー。

Flask等の外部Webフレームワークは使わず、標準ライブラリのみで動作する。
組織内LAN上の少人数での利用を想定し、認証は行わない。

使い方:
    python server.py
    → 同じLAN内の端末から http://<このPCのIPアドレス>:8090 にアクセス
"""

import base64
import datetime
import functools
import json
import pathlib
import queue
import re
import threading
import time
import uuid
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from transcribe import build_output_paths, load_model, save_results, transcribe

HOST = "0.0.0.0"
PORT = 8090

PROJECT_DIR = pathlib.Path(__file__).resolve().parent
INPUT_DIR = PROJECT_DIR / "input"
OUTPUT_DIR = PROJECT_DIR / "output"
WEB_DIR = PROJECT_DIR / "web"

# アップロード音声・文字起こし結果は個人情報を含み得るため、一定日数で自動削除する
RETENTION_DAYS = 30

# 1リクエストで受け付けるアップロードの上限（Base64化前の目安、約500MB）
MAX_CONTENT_LENGTH = 500 * 1024 * 1024

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
JOB_QUEUE: "queue.Queue[str]" = queue.Queue()

_model_cache: dict[str, object] = {}
_model_cache_lock = threading.Lock()


def get_model(model_size: str, on_downloading=None):
    with _model_cache_lock:
        if model_size not in _model_cache:
            _model_cache[model_size] = load_model(model_size, on_downloading=on_downloading)
        return _model_cache[model_size]


def cleanup_old_files(directory: pathlib.Path, days: int) -> None:
    """directory直下のファイルのうち、更新日時がdays日より古いものを削除する"""
    cutoff = time.time() - days * 86400
    for path in directory.iterdir():
        if path.name == ".gitkeep" or not path.is_file():
            continue
        if path.stat().st_mtime < cutoff:
            path.unlink()


def worker_loop() -> None:
    while True:
        job_id = JOB_QUEUE.get()
        job = JOBS[job_id]
        try:
            with JOBS_LOCK:
                job["status"] = "running"

            def on_downloading(job=job):
                with JOBS_LOCK:
                    job["status"] = "downloading_model"

            model = get_model(job["model"], on_downloading=on_downloading)

            with JOBS_LOCK:
                job["status"] = "running"

            audio_path = pathlib.Path(job["audio_path"])
            # 出力ファイル名は job_id ではなく元のアップロードファイル名から生成する
            display_name = pathlib.Path(job["filename"])
            output_path, formatted_path = build_output_paths(display_name, job["model"])

            def on_segment(segment, info, job=job):
                if info.duration:
                    with JOBS_LOCK:
                        job["progress"] = round(min(segment.end / info.duration, 1.0), 2)

            timestamped_lines, texts = transcribe(
                model, audio_path, job["language"], on_segment=on_segment
            )
            save_results(output_path, formatted_path, timestamped_lines, texts)

            with JOBS_LOCK:
                job.update(
                    status="done",
                    progress=1.0,
                    output_path=str(output_path),
                    formatted_path=str(formatted_path),
                )
        except Exception as e:
            with JOBS_LOCK:
                job.update(status="error", error=str(e))
        finally:
            JOB_QUEUE.task_done()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # アクセスログを抑制（RAG_met/web_app.pyと同様）
        pass

    def do_GET(self):
        parsed = urlparse(self.path)

        m = re.match(r"^/api/jobs/([a-f0-9]+)/download$", parsed.path)
        if m:
            return self._handle_download(m.group(1), parse_qs(parsed.query))

        m = re.match(r"^/api/jobs/([a-f0-9]+)$", parsed.path)
        if m:
            return self._handle_status(m.group(1))

        super().do_GET()

    def do_POST(self):
        if self.path == "/api/jobs":
            return self._handle_submit()
        self._json(404, {"error": "not found"})

    def _handle_submit(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_CONTENT_LENGTH:
            return self._json(413, {"error": "ファイルサイズが大きすぎます"})

        body = json.loads(self.rfile.read(length))
        filename = pathlib.Path(body.get("filename", "audio")).name
        model_size = body.get("model") or "small"
        language = body.get("language") or None

        try:
            audio_bytes = base64.b64decode(body["audio_base64"])
        except (KeyError, ValueError):
            return self._json(400, {"error": "音声データが不正です"})

        job_id = uuid.uuid4().hex[:12]
        audio_path = INPUT_DIR / f"{job_id}_{filename}"
        audio_path.write_bytes(audio_bytes)

        with JOBS_LOCK:
            JOBS[job_id] = {
                "status": "pending",
                "filename": filename,
                "model": model_size,
                "language": language,
                "audio_path": str(audio_path),
                "progress": 0.0,
                "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
                "error": None,
                "output_path": None,
                "formatted_path": None,
            }
        JOB_QUEUE.put(job_id)
        self._json(202, {"job_id": job_id})

    def _handle_status(self, job_id):
        job = JOBS.get(job_id)
        if not job:
            return self._json(404, {"error": "指定されたジョブが見つかりません"})
        public_fields = (
            "status",
            "filename",
            "model",
            "language",
            "progress",
            "created_at",
            "error",
        )
        self._json(200, {k: job[k] for k in public_fields})

    def _handle_download(self, job_id, query):
        job = JOBS.get(job_id)
        if not job or job["status"] != "done":
            return self._json(404, {"error": "結果はまだ準備できていません"})

        kind = query.get("type", ["timestamped"])[0]
        path = pathlib.Path(
            job["formatted_path"] if kind == "formatted" else job["output_path"]
        )
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{path.name}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    cleanup_old_files(INPUT_DIR, RETENTION_DAYS)
    cleanup_old_files(OUTPUT_DIR, RETENTION_DAYS)

    threading.Thread(target=worker_loop, daemon=True).start()

    handler = functools.partial(Handler, directory=str(WEB_DIR))
    httpd = ThreadingHTTPServer((HOST, PORT), handler)
    print(f"サーバー起動: http://localhost:{PORT}（同じLAN内の他端末からもアクセス可能）")
    print("終了するには Ctrl+C を押してください")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n終了しました")


if __name__ == "__main__":
    main()
