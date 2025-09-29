from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from gamecenter.streetBattle.resource_manager import (
    DEFAULT_PREFERRED_FORMATS,
    PROJECT_ROOT,
    ResourceManager,
)
from gamecenter.streetBattle.sketchfab_tools.conversion import ConversionResult


class StubConverter:
    def convert(self, *, source_path: Path, output_path: Path, animations_dir: Path, working_dir: Path) -> ConversionResult:
        output_path.write_bytes(b"bam")
        animations_dir.mkdir(parents=True, exist_ok=True)
        idle = animations_dir / "Idle.bam"
        idle.write_bytes(b"idle")
        return ConversionResult(
            bam_path=output_path,
            animation_paths=[idle],
            command=["stub"],
            duration=0.01,
            stdout="",
            stderr="",
        )


def _build_catalog(path: Path) -> None:
    catalog = {
        "kyo_kusanagi": {
            "name": "Kyo Kusanagi",
            "sketchfab": {"uid": "demo123"},
        }
    }
    path.write_text(json.dumps(catalog), encoding="utf-8")


@pytest.fixture()
def temp_manager(tmp_path: Path) -> ResourceManager:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "characters").mkdir()
    (assets_dir / "models").mkdir()
    (assets_dir / "downloads").mkdir()

    _build_catalog(assets_dir / "resource_catalog.json")
    (assets_dir / "presigned_urls.json").write_text("{}", encoding="utf-8")
    (assets_dir / "characters_manifest.json").write_text("{}", encoding="utf-8")

    manager = ResourceManager(assets_dir=assets_dir, project_root=PROJECT_ROOT)
    manager.converter = StubConverter()
    return manager


def _create_zip_with_gltf(zip_path: Path, character_id: str) -> None:
    with zipfile.ZipFile(zip_path, "w") as zf:
        gltf_payload = {
            "asset": {"version": "2.0"},
            "scenes": [0],
            "nodes": [{"mesh": 0}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
        }
        zf.writestr(f"{character_id}/scene.gltf", json.dumps(gltf_payload))
        zf.writestr(f"{character_id}/scene.bin", "binary-data")


def test_process_local_archive_creates_bam_and_animations(temp_manager: ResourceManager) -> None:
    manager = temp_manager
    zip_path = manager.downloads_dir / "kyo_kusanagi.zip"
    _create_zip_with_gltf(zip_path, "kyo_kusanagi")

    success = manager._process_local_archive(  # pylint: disable=protected-access
        "kyo_kusanagi",
        zip_path,
        preferred_formats=DEFAULT_PREFERRED_FORMATS,
        keep_archive=True,
    )

    assert success is True
    target_dir = manager.characters_dir / "kyo_kusanagi" / "sketchfab"
    assert (target_dir / "kyo_kusanagi.bam").exists()
    assert (target_dir / "animations" / "Idle.bam").exists()
    assert (target_dir / "animations" / "idle.bam").exists()


def test_resolve_presigned_url_prefers_character_entry(temp_manager: ResourceManager) -> None:
    manager = temp_manager
    manager.presigned_map = {
        "kyo_kusanagi": "https://example.com/direct"
    }
    assert manager._resolve_presigned_url("kyo_kusanagi") == "https://example.com/direct"  # pylint: disable=protected-access

    manager.presigned_map = {
        "demo123": "https://example.com/from_uid"
    }
    assert manager._resolve_presigned_url("kyo_kusanagi") == "https://example.com/from_uid"  # pylint: disable=protected-access
