from pathlib import Path
from typing import Any

import requests

from client.config import API_KEY, REQUEST_TIMEOUT, SERVER_URL

# =========================================================
# API 客户端
# =========================================================
# 客户端所有功能都通过 HTTP 调用服务器完成：
# 创建数据集、上传图片、上传模型、调用 YOLO 检测、获取检测结果。
# =========================================================


class ApiError(RuntimeError):
    # 接口调用失败时抛出的异常。
    pass


class LocoRoofApiClient:
    # 机车车顶异物识别系统 API 客户端。

    def __init__(self, server_url: str = SERVER_URL, api_key: str = API_KEY):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key

    @property
    def headers(self) -> dict[str, str]:
        # 统一请求头，携带 API Key。
        return {"X-API-Key": self.api_key}

    def _url(self, path: str) -> str:
        # 拼接完整 URL。
        return f"{self.server_url}{path}"

    def _request(self, method: str, path: str, **kwargs) -> Any:
        # 统一请求入口，集中处理连接错误和接口错误。
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        headers = kwargs.pop("headers", {})
        headers.update(self.headers)
        kwargs["headers"] = headers

        try:
            resp = requests.request(method, self._url(path), **kwargs)
        except requests.RequestException as exc:
            raise ApiError(f"无法连接服务器：{exc}") from exc

        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise ApiError(f"接口错误 {resp.status_code}：{detail}")

        if resp.content:
            return resp.json()
        return None

    def health(self) -> dict:
        # 测试服务器是否在线。
        try:
            resp = requests.get(self._url("/health"), timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            raise ApiError(f"服务器连接失败：{exc}") from exc

    def create_dataset(self, name: str, description: str = "") -> dict:
        return self._request("POST", "/api/datasets", json={"name": name, "description": description})

    def list_datasets(self) -> list[dict]:
        return self._request("GET", "/api/datasets")

    def upload_image(self, dataset_id: int, image_path: str | Path, split: str = "test") -> dict:
        # 上传图片到服务器。
        image_path = Path(image_path)
        with image_path.open("rb") as f:
            files = {"file": (image_path.name, f)}
            data = {"split": split}
            return self._request("POST", f"/api/datasets/{dataset_id}/images", files=files, data=data)

    def list_images(self, dataset_id: int, split: str | None = None) -> list[dict]:
        params = {}
        if split:
            params["split"] = split
        return self._request("GET", f"/api/datasets/{dataset_id}/images", params=params)

    def upload_model(self, name: str, model_path: str | Path, active: bool = True) -> dict:
        # 上传 .pt 模型到服务器。
        model_path = Path(model_path)
        with model_path.open("rb") as f:
            files = {"file": (model_path.name, f)}
            data = {"name": name, "active": str(active).lower()}
            return self._request("POST", "/api/models/upload", files=files, data=data)

    def list_models(self) -> list[dict]:
        return self._request("GET", "/api/models")

    def activate_model(self, model_id: int) -> dict:
        return self._request("POST", f"/api/models/{model_id}/activate")

    def detect_image(self, image_id: int, conf: float = 0.25, model_id: int | None = None) -> dict:
        # 调用服务器检测某张图片。
        params = {"conf": conf}
        if model_id is not None:
            params["model_id"] = model_id
        return self._request("POST", f"/api/images/{image_id}/detect", params=params)

    def get_stats(self) -> dict:
        return self._request("GET", "/api/stats")

    def download_bytes(self, url: str) -> bytes:
        # 下载图片字节，用于 PySide6 显示图片。
        # 这里做 URL 容错：如果服务器返回的 URL 没有 http://，客户端自动补上。
        if url.startswith("/"):
            url = f"{self.server_url}{url}"
        elif not url.startswith(("http://", "https://")):
            url = f"http://{url}"

        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as exc:
            raise ApiError(f"图片下载失败：{exc}") from exc