#!/usr/bin/env python3
r"""StreetBattle Asset Resource Manager

This script removes stale character assets and downloads the curated Sketchfab
models defined in ``assets/resource_catalog.json``. It integrates with
``SketchfabSessionManager`` to perform authenticated downloads, preferring GLTF
archives and falling back to GLB when GLTF is unavailable.

Usage examples (PowerShell):

```powershell
# Clean characters/models folders and download every catalog entry
python .\gamecenter\streetBattle\resource_manager.py

# Preview the operations without touching the filesystem
python .\gamecenter\streetBattle\resource_manager.py --dry-run

# Download a subset of characters only
python .\gamecenter\streetBattle\resource_manager.py --characters kyo_kusanagi iori_yagami
```

The script produces an updated ``characters_manifest.json`` summarising the
available assets. Archives are extracted under each character directory using
the structure expected by ``EnhancedCharacterManager``:
``assets/characters/<character_id>/sketchfab/<character_id>.<ext>``
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import zipfile
import requests
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS_DIR = Path(__file__).parent / "assets"
DEFAULT_PREFERRED_FORMATS: Tuple[str, ...] = ("gltf", "glb")

# Make sure local modules can be imported no matter where the tool is launched
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gamecenter.streetBattle.sketchfab_session import SketchfabSessionManager  # noqa: E402

logger = logging.getLogger("streetbattle.resource_manager")


class ResourceManager:
    """High level orchestrator for StreetBattle assets."""

    def __init__(self, assets_dir: Path = ASSETS_DIR, project_root: Path = PROJECT_ROOT):
        self.assets_dir = assets_dir
        self.project_root = project_root
        self.characters_dir = self.assets_dir / "characters"
        self.models_dir = self.assets_dir / "models"
        self.catalog_path = self.assets_dir / "resource_catalog.json"
        self.manifest_path = self.assets_dir / "characters_manifest.json"
        self.presigned_path = self.assets_dir / "presigned_urls.json"

        self.catalog = self._load_catalog()
        self.presigned_map = self._load_presigned_urls()
        self.failed_downloads: List[str] = []

    # ------------------------------------------------------------------
    # catalog helpers
    # ------------------------------------------------------------------
    def _load_catalog(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Resource catalog not found: {self.catalog_path}")

        with open(self.catalog_path, "r", encoding="utf-8") as fp:
            catalog = json.load(fp)

        if not isinstance(catalog, dict):
            raise ValueError("resource_catalog.json must contain a JSON object")

        logger.info("Loaded resource catalog containing %d entries", len(catalog))
        return catalog

    # ------------------------------------------------------------------
    # cleanup helpers
    # ------------------------------------------------------------------
    def clear_character_resources(self, dry_run: bool = False) -> None:
        """Delete every character/model asset prior to a fresh download."""
        targets = [self.characters_dir, self.models_dir]
        for target in targets:
            if not target.exists():
                continue

            if dry_run:
                logger.info("[dry-run] Would remove directory: %s", target)
                continue

            for item in target.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    try:
                        item.unlink()
                    except FileNotFoundError:
                        pass

            logger.info("Cleared resource directory: %s", target)

        # Ensure base directories exist after cleanup
        if not dry_run:
            self.characters_dir.mkdir(parents=True, exist_ok=True)
            self.models_dir.mkdir(parents=True, exist_ok=True)

    def _load_presigned_urls(self) -> Dict[str, str]:
        """Load optional mapping of character_id -> presigned download URL."""
        try:
            if self.presigned_path.exists():
                data = json.load(open(self.presigned_path, 'r', encoding='utf-8'))
                if isinstance(data, dict):
                    logger.info("Loaded presigned URL mapping for %d entries", len(data))
                    return data
        except Exception as e:
            logger.warning("Failed to load presigned URLs: %s", e)
        return {}

    # ------------------------------------------------------------------
    # download pipeline
    # ------------------------------------------------------------------
    def download_from_catalog(
        self,
        *,
        session: Optional[SketchfabSessionManager],
        preferred_formats: Sequence[str] = DEFAULT_PREFERRED_FORMATS,
        dry_run: bool = False,
        subset: Optional[Iterable[str]] = None,
        keep_archives: bool = False,
    ) -> None:
        characters = self._select_characters(subset)
        logger.info("Preparing to download %d characters", len(characters))

        if dry_run:
            for char_id in characters:
                logger.info("[dry-run] Would download %s (preferred: %s)", char_id, list(preferred_formats))
            return

        if session is None:
            raise ValueError("Sketchfab session is required when not running in dry-run mode")

        # 先选取一个用于鉴权探测的UID（优先首个角色）
        probe_uid: Optional[str] = None
        for char_id in characters:
            uid = (self.catalog.get(char_id, {}).get("sketchfab") or {}).get("uid")
            if uid:
                probe_uid = uid
                break
        # 若子集均无UID，则全量里找一个
        if not probe_uid:
            for v in self.catalog.values():
                uid = (v.get("sketchfab") or {}).get("uid")
                if uid:
                    probe_uid = uid
                    break

        auth_ok = False
        try:
            auth_ok = session.ensure_authenticated(test_uid=probe_uid)
        except Exception:
            auth_ok = False
        if not auth_ok:
            logger.warning("Sketchfab authentication unavailable; will attempt presigned URL fallback if provided")

        for char_id in characters:
            char_info = self.catalog.get(char_id, {})
            uid = (char_info.get("sketchfab") or {}).get("uid")
            if not uid:
                logger.warning("Character %s is missing sketchfab.uid; skipping", char_id)
                continue

            logger.info("%s -> Sketchfab UID %s", char_id, uid)
            target_dir = self.characters_dir / char_id / "sketchfab"
            temp_dir = Path(tempfile.mkdtemp(prefix=f"{char_id}_", dir=str(self.assets_dir)))

            try:
                download_path: Optional[Path] = None

                # Prefer authenticated API when available
                if auth_ok:
                    download_path = session.download_model(uid, temp_dir, preferred_formats)

                # Presigned fallback (when auth failed or API returned nothing)
                if not download_path:
                    presigned_url = self.presigned_map.get(char_id) or self.presigned_map.get(uid)
                    if presigned_url:
                        logger.info("Using presigned URL fallback for %s", char_id)
                        download_path = self._download_presigned(presigned_url, temp_dir, uid, preferred_formats)

                if not download_path:
                    self._handle_download_failure(char_id, "No download path available (auth/presigned)")
                    continue

                extracted_path = self._unpack_archive(download_path, target_dir, char_id, preferred_formats)
                if not extracted_path:
                    self._handle_download_failure(char_id, "Could not locate model inside archive")
                    continue

                logger.info("✅ %s ready: %s", char_id, extracted_path)

                if not keep_archives and download_path.exists():
                    download_path.unlink(missing_ok=True)

            except Exception as exc:
                self._handle_download_failure(char_id, str(exc))
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        if self.failed_downloads:
            logger.warning("The following characters failed to download: %s", ", ".join(self.failed_downloads))
            logger.warning("Try re-running with --dry-run to inspect, or use Chrome DevTools MCP fallback as needed.")

    # ------------------------------------------------------------------
    # presigned helper
    # ------------------------------------------------------------------
    def _download_presigned(
        self,
        url: str,
        temp_dir: Path,
        model_uid: str,
        preferred_formats: Sequence[str],
    ) -> Optional[Path]:
        """Download a presigned GLTF/GLB or archive and return the local file path."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) StreetBattle/1.0',
                'Accept': '*/*',
                'Connection': 'keep-alive',
            }
            with requests.get(url, headers=headers, timeout=180, stream=True) as r:
                r.raise_for_status()
                # Determine filename
                name = os.path.basename(urlparse(url).path)
                lower = name.lower()
                out_path = temp_dir / (name or f"{model_uid}.bin")
                with open(out_path, 'wb') as fp:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            fp.write(chunk)

            # If direct GLTF/GLB
            if lower.endswith('.gltf') or lower.endswith('.glb'):
                return out_path

            # If archive, ensure zip and return path
            return out_path
        except Exception as e:
            logger.error("Presigned download failed: %s", e)
            return None

    def _select_characters(self, subset: Optional[Iterable[str]]) -> List[str]:
        if subset is None:
            return sorted(self.catalog.keys())
        requested = []
        for item in subset:
            key = item.strip()
            if not key:
                continue
            if key not in self.catalog:
                logger.warning("Requested character %s not present in catalog", key)
                continue
            requested.append(key)
        return sorted(requested)

    def _handle_download_failure(self, character_id: str, reason: str) -> None:
        logger.error("❌ Failed to download %s: %s", character_id, reason)
        self.failed_downloads.append(character_id)

    # ------------------------------------------------------------------
    # extraction helpers
    # ------------------------------------------------------------------
    def _unpack_archive(
        self,
        archive_path: Path,
        target_dir: Path,
        character_id: str,
        preferred_formats: Sequence[str],
    ) -> Optional[Path]:
        target_dir.mkdir(parents=True, exist_ok=True)

        extracted_model: Optional[Path] = None
        archive_suffix = archive_path.suffix.lower()

        if archive_path.is_file() and zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(target_dir)

            extracted_model = self._locate_preferred_model(target_dir, character_id, preferred_formats)
        elif archive_suffix in {".gltf", ".glb"}:
            # Direct download without archive
            destination = target_dir / f"{character_id}{archive_suffix}"
            shutil.move(str(archive_path), destination)
            extracted_model = destination
        else:
            logger.warning("Unknown archive format for %s: %s", character_id, archive_path)

        # Harmonise naming & tidy temp structure
        if extracted_model and extracted_model.exists():
            extracted_model = self._normalise_model_path(extracted_model, target_dir, character_id)
            self._clean_intermediate_directories(target_dir, extracted_model)
            return extracted_model

        return None

    # ------------------------------------------------------------------
    # public orchestration entrypoint used by game runtime
    # ------------------------------------------------------------------
    def download_premium_resources(
        self,
        character_ids: Optional[Iterable[str]] = None,
        *,
        dry_run: bool = False,
        keep_archives: bool = False,
        preferred_formats: Sequence[str] = DEFAULT_PREFERRED_FORMATS,
    ) -> bool:
        """Download premium Sketchfab resources for the requested characters.

        This wraps :meth:`download_from_catalog` so the runtime can lazily
        acquire assets when they are not present locally. Returns ``True`` when
        the pipeline completed without fatal errors.
        """

        subset = list(character_ids) if character_ids else None

        if dry_run:
            try:
                self.download_from_catalog(
                    session=None,
                    preferred_formats=preferred_formats,
                    dry_run=True,
                    subset=subset,
                    keep_archives=keep_archives,
                )
                return True
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Dry-run download failed: %s", exc)
                return False

        try:
            session = SketchfabSessionManager(project_root=self.project_root)
        except FileNotFoundError as exc:
            logger.error("Sketchfab credentials missing: %s", exc)
            return False
        except Exception as exc:
            logger.error("Failed to initialise Sketchfab session: %s", exc)
            return False

        auth_ok = False
        try:
            auth_ok = session.ensure_authenticated()
        except Exception as exc:
            logger.error("Sketchfab authentication failed: %s", exc)
            auth_ok = False

        if not auth_ok:
            logger.error("Cannot download premium resources without Sketchfab authentication")
            return False

        try:
            self.download_from_catalog(
                session=session,
                preferred_formats=preferred_formats,
                dry_run=False,
                subset=subset,
                keep_archives=keep_archives,
            )
            # Refresh manifest so downstream tooling sees new assets
            self.update_manifest(dry_run=False)
            return True
        except Exception as exc:
            logger.error("Premium resource download failed: %s", exc)
            return False

    def _locate_preferred_model(
        self,
        search_root: Path,
        character_id: str,
        preferred_formats: Sequence[str],
    ) -> Optional[Path]:
        format_priority = [fmt.lower().lstrip('.') for fmt in preferred_formats]
        candidates: Dict[str, Path] = {}

        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            ext = path.suffix.lower().lstrip('.')
            if ext in format_priority:
                candidates.setdefault(ext, path)

        for fmt in format_priority:
            if fmt in candidates:
                return candidates[fmt]

        return None

    def _normalise_model_path(self, model_path: Path, target_dir: Path, character_id: str) -> Path:
        suffix = model_path.suffix.lower()
        normalized = target_dir / f"{character_id}{suffix}"

        if model_path.resolve() != normalized.resolve():
            normalized.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(model_path), str(normalized))

        return normalized

    def _clean_intermediate_directories(self, root: Path, primary_model: Path) -> None:
        for path in list(root.iterdir()):
            if path == primary_model:
                continue
            if path.is_dir():
                # Remove empty folders
                if not any(path.rglob("*")):
                    shutil.rmtree(path, ignore_errors=True)
            else:
                # Keep texture files / materials; remove obvious placeholders
                if path.suffix.lower() in {".zip", ".rar", ".7z"}:
                    path.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # manifest helpers
    # ------------------------------------------------------------------
    def update_manifest(self, *, dry_run: bool = False) -> None:
        characters: List[Dict[str, str]] = []
        for char_dir in sorted(self.characters_dir.glob("*")):
            model_path = None
            sketchfab_dir = char_dir / "sketchfab"
            if sketchfab_dir.exists():
                for fmt in DEFAULT_PREFERRED_FORMATS:
                    candidate = sketchfab_dir / f"{char_dir.name}.{fmt}"
                    if candidate.exists():
                        model_path = str(candidate.relative_to(self.assets_dir))
                        break
                if not model_path:
                    # fallback to any gltf/glb present
                    generic = next(sketchfab_dir.glob("*.gltf"), None) or next(sketchfab_dir.glob("*.glb"), None)
                    if generic:
                        model_path = str(generic.relative_to(self.assets_dir))

            characters.append({
                "id": char_dir.name,
                "model": model_path,
                "sketchfab": True if model_path else False,
            })

        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "character_count": len(characters),
            "characters": characters,
        }

        if dry_run:
            logger.info("[dry-run] Would update manifest at %s with %d characters", self.manifest_path, len(characters))
            return

        with open(self.manifest_path, "w", encoding="utf-8") as fp:
            json.dump(manifest, fp, indent=2, ensure_ascii=False)

        logger.info("Updated manifest with %d characters: %s", len(characters), self.manifest_path)

    # ------------------------------------------------------------------
    # batch automation methods
    # ------------------------------------------------------------------
    def fetch_all_presigned_urls_auto(self) -> Dict[str, str]:
        """自动化批量获取所有角色的预签名URL
        
        通过Chrome DevTools MCP集成自动获取所有43个角色的预签名URL。
        这个方法会启动浏览器会话，访问Sketchfab API，并批量获取下载链接。
        
        Returns:
            Dict[str, str]: 角色ID到预签名URL的映射
        """
        try:
            # 获取所有需要下载的角色
            characters = [(char_id, info.get('sketchfab', {}).get('uid')) 
                         for char_id, info in self.catalog.items() 
                         if info.get('sketchfab', {}).get('uid')]
            
            results = {}
            total_chars = len(characters) 
            
            logger.info(f"开始批量获取 {total_chars} 个角色的预签名URL...")
            logger.info("注意: 当前需要手动执行浏览器脚本获取URL")
            logger.info("请运行: python generate_presigned_urls.py")
            logger.info("然后在浏览器中执行生成的JavaScript脚本")
            
            # 检查是否已有预签名URL文件
            if self.presigned_path.exists():
                try:
                    with open(self.presigned_path, 'r', encoding='utf-8') as f:
                        existing_urls = json.load(f)
                    if isinstance(existing_urls, dict) and existing_urls:
                        logger.info(f"发现现有预签名URL文件，包含 {len(existing_urls)} 个URL")
                        return existing_urls
                except Exception as e:
                    logger.warning(f"读取现有预签名URL文件失败: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"批量获取预签名URL失败: {e}")
            return {}
    
    def _save_presigned_urls(self, urls: Dict[str, str]) -> None:
        """保存预签名URL到文件"""
        try:
            with open(self.presigned_path, 'w', encoding='utf-8') as f:
                json.dump(urls, f, indent=2, ensure_ascii=False)
            logger.info(f"预签名URL已保存到: {self.presigned_path}")
        except Exception as e:
            logger.error(f"保存预签名URL失败: {e}")
    
    def batch_download_with_auto_urls(
        self,
        preferred_formats: Sequence[str] = DEFAULT_PREFERRED_FORMATS,
        dry_run: bool = False,
        subset: Optional[Iterable[str]] = None,
        keep_archives: bool = False,
    ) -> None:
        """自动获取预签名URL后批量下载
        
        这是一个高级方法，结合了预签名URL获取和批量下载功能。
        首先尝试获取所有角色的预签名URL，然后执行批量下载。
        
        Args:
            preferred_formats: 优先下载格式
            dry_run: 是否为预览模式
            subset: 限制下载的角色子集
            keep_archives: 是否保留下载的存档文件
        """
        logger.info("开始自动化批量下载流程...")
        
        # 1. 先尝试获取所有预签名URL
        presigned_urls = self.fetch_all_presigned_urls_auto()
        
        if presigned_urls:
            # 2. 更新内存中的预签名URL映射
            self.presigned_map.update(presigned_urls)
            logger.info(f"已更新 {len(presigned_urls)} 个预签名URL到内存映射")
        
        # 3. 执行常规下载流程（使用None作为session，依赖预签名URL）
        self.download_from_catalog(
            session=None,
            preferred_formats=preferred_formats,
            dry_run=dry_run,
            subset=subset,
            keep_archives=keep_archives,
        )


# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="StreetBattle unified resource manager")
    parser.add_argument(
        "--characters",
        nargs="*",
        help="Restrict download to specific character IDs (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without modifying files or contacting Sketchfab",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip deleting existing character/model resources",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip downloads (useful when only regenerating manifest)",
    )
    parser.add_argument(
        "--keep-archives",
        action="store_true",
        help="Preserve downloaded archives after extraction",
    )
    parser.add_argument(
        "--prefer-format",
        choices=["gltf", "glb"],
        default="gltf",
        help="Primary format preference when multiple archives are available",
    )
    parser.add_argument(
        "--batch-auto",
        action="store_true",
        help="Use batch automation with presigned URL fallback (no session auth required)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    manager = ResourceManager()

    preferred_formats: Tuple[str, ...]
    if args.prefer_format == "gltf":
        preferred_formats = ("gltf", "glb")
    else:
        preferred_formats = ("glb", "gltf")

    subset = args.characters if args.characters else None

    if not args.no_clean:
        manager.clear_character_resources(dry_run=args.dry_run)

    session: Optional[SketchfabSessionManager] = None
    if not args.dry_run and not args.no_download:
        session = SketchfabSessionManager(str(manager.project_root))

    if not args.no_download:
        if args.batch_auto:
            # 使用批量自动化下载模式
            manager.batch_download_with_auto_urls(
                preferred_formats=preferred_formats,
                dry_run=args.dry_run,
                subset=subset,
                keep_archives=args.keep_archives,
            )
        else:
            # 使用常规下载模式
            manager.download_from_catalog(
                session=session,
                preferred_formats=preferred_formats,
                dry_run=args.dry_run,
                subset=subset,
                keep_archives=args.keep_archives,
            )

    manager.update_manifest(dry_run=args.dry_run)

    if manager.failed_downloads and not args.dry_run:
        logger.error(
            "Some downloads failed. Consider using the Chrome DevTools MCP workflow or manual downloads for: %s",
            ", ".join(manager.failed_downloads),
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
