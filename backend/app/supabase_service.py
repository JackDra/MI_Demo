from __future__ import annotations

import json
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from pydantic import BaseModel


class MapAsset(BaseModel):
    url: str
    storage_bucket: str | None = None
    storage_path: str | None = None
    source: str


@dataclass
class SupabaseService:
    supabase_url: str | None = None
    service_role_key: str | None = None
    storage_bucket: str = "mi-demo-assets"

    @classmethod
    def from_env(cls) -> SupabaseService:
        return cls(
            supabase_url=os.getenv("SUPABASE_URL"),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            storage_bucket=os.getenv("SUPABASE_STORAGE_BUCKET", "mi-demo-assets"),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.service_role_key)

    def ensure_topographic_map_asset(
        self,
        local_path: Path,
        storage_path: str = "maps/murrumbidgee-opentopomap-z10.png",
        fallback_url: str = "/maps/murrumbidgee-opentopomap-z10.png",
    ) -> MapAsset:
        if not self.is_configured:
            return MapAsset(url=fallback_url, source="local")

        if not local_path.exists():
            raise FileNotFoundError(f"Topographic map asset not found: {local_path}")

        self._ensure_public_bucket()
        self._upload_file(local_path, storage_path)
        return MapAsset(
            url=self.public_storage_url(storage_path),
            storage_bucket=self.storage_bucket,
            storage_path=storage_path,
            source="supabase-storage",
        )

    def public_storage_url(self, storage_path: str) -> str:
        return (
            f"{self._storage_base_url()}/object/public/"
            f"{quote(self.storage_bucket, safe='')}/{quote(storage_path, safe='/')}"
        )

    def _ensure_public_bucket(self) -> None:
        response = self._request("GET", f"/bucket/{quote(self.storage_bucket, safe='')}")
        if response is not None:
            return

        payload = {
            "id": self.storage_bucket,
            "name": self.storage_bucket,
            "public": True,
            "file_size_limit": 10 * 1024 * 1024,
            "allowed_mime_types": ["image/png"],
        }
        self._request("POST", "/bucket", json_body=payload, expected_statuses={200, 201})

    def _upload_file(self, local_path: Path, storage_path: str) -> None:
        content_type = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
        self._request(
            "POST",
            f"/object/{quote(self.storage_bucket, safe='')}/{quote(storage_path, safe='/')}",
            body=local_path.read_bytes(),
            headers={
                "cache-control": "3600",
                "content-type": content_type,
                "x-upsert": "true",
            },
            expected_statuses={200, 201},
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> dict[str, Any] | None:
        if not self.service_role_key:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")

        expected_statuses = expected_statuses or {200}
        request_body = body
        request_headers = {
            "apikey": self.service_role_key,
            "authorization": f"Bearer {self.service_role_key}",
            **(headers or {}),
        }
        if json_body is not None:
            request_body = json.dumps(json_body).encode("utf-8")
            request_headers["content-type"] = "application/json"

        request = Request(
            f"{self._storage_base_url()}{path}",
            data=request_body,
            headers=request_headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=20) as response:
                if response.status not in expected_statuses:
                    raise RuntimeError(f"Supabase Storage returned status {response.status}")
                content = response.read()
        except HTTPError as exc:
            if method == "GET" and exc.code == 404:
                return None
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Supabase Storage request failed with status {exc.code}: {error_body}"
            ) from exc

        if not content:
            return {}
        return json.loads(content.decode("utf-8"))

    def _storage_base_url(self) -> str:
        if not self.supabase_url:
            raise RuntimeError("SUPABASE_URL is not configured")
        return f"{self.supabase_url.rstrip('/')}/storage/v1"
