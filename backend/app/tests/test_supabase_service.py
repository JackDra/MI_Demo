from pathlib import Path

from app.supabase_service import SupabaseService


class RecordingSupabaseService(SupabaseService):
    bucket_checked = False
    uploaded_path: Path | None = None
    uploaded_storage_path: str | None = None

    def _ensure_public_bucket(self) -> None:
        self.bucket_checked = True

    def _upload_file(self, local_path: Path, storage_path: str) -> None:
        self.uploaded_path = local_path
        self.uploaded_storage_path = storage_path


def test_topographic_asset_upload_returns_public_storage_url(tmp_path: Path) -> None:
    map_file = tmp_path / "map.png"
    map_file.write_bytes(b"png")
    service = RecordingSupabaseService(
        supabase_url="https://example.supabase.co",
        service_role_key="service-role",
        storage_bucket="assets",
    )

    asset = service.ensure_topographic_map_asset(map_file)

    assert service.bucket_checked
    assert service.uploaded_path == map_file
    assert service.uploaded_storage_path == "maps/murrumbidgee-opentopomap-z10.png"
    assert asset.source == "supabase-storage"
    assert asset.storage_bucket == "assets"
    assert asset.url == (
        "https://example.supabase.co/storage/v1/object/public/"
        "assets/maps/murrumbidgee-opentopomap-z10.png"
    )
