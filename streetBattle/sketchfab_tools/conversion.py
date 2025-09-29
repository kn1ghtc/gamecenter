"""Utilities for converting GLTF/GLB assets to Panda3D BAM files."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import logging

__all__ = [
    "ConversionError",
    "ConversionResult",
    "Gltf2BamConverter",
]

logger = logging.getLogger("streetbattle.sketchfab.conversion")


class ConversionError(RuntimeError):
    """Raised when a GLTF to BAM conversion fails."""


@dataclass
class ConversionResult:
    """Metadata describing a conversion run."""

    bam_path: Path
    animation_paths: List[Path]
    command: List[str]
    duration: float
    stdout: str
    stderr: str


class Gltf2BamConverter:
    """Wrapper around the ``gltf2bam`` CLI used by Panda3D."""

    def __init__(
        self,
        command: Optional[Iterable[str] | str] = None,
        *,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 300.0,
        textures: Optional[str] = "ref",
        extra_args: Optional[Sequence[str]] = None,
    ) -> None:
        self.base_command = self._resolve_command(command)
        self.timeout = timeout
        self.env = env or {}
        self.textures = textures
        self.extra_args = list(extra_args) if extra_args else []

    @staticmethod
    def _resolve_command(command: Optional[Iterable[str] | str]) -> List[str]:
        if command:
            if isinstance(command, str):
                return shlex.split(command)
            return list(command)

        env_value = os.getenv("GLTF2BAM_PATH")
        if env_value:
            return shlex.split(env_value)
        return ["gltf2bam"]

    def convert(
        self,
        *,
        source_path: Path,
        output_path: Path,
        animations_dir: Path,
        working_dir: Optional[Path] = None,
    ) -> ConversionResult:
        source_path = Path(source_path)
        output_path = Path(output_path)
        animations_dir = Path(animations_dir)

        if not source_path.exists():
            raise ConversionError(f"Source model not found: {source_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        animations_dir.mkdir(parents=True, exist_ok=True)

        # Remove stale animation files so we can detect fresh outputs
        for stale in animations_dir.glob("*.bam"):
            try:
                stale.unlink()
            except OSError:
                logger.warning("Failed to remove stale animation file: %s", stale)

        command = list(self.base_command)

        if self.textures:
            command.extend(["--textures", self.textures])

        command.extend(["--animations", "separate"])
        command.extend(self.extra_args)
        command.append(str(source_path))
        command.append(str(output_path))

        env = os.environ.copy()
        env.update(self.env)

        # Set working directory to the animations directory so separate animations are output there
        cwd = animations_dir

        logger.info("Running gltf2bam for %s", source_path.name)
        start = time.perf_counter()
        try:
            completed = subprocess.run(  # noqa: S603
                command,
                cwd=str(cwd),
                check=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )
        except FileNotFoundError as exc:
            raise ConversionError(
                "gltf2bam executable not found. Ensure Panda3D tools are installed and GLTF2BAM_PATH is configured."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ConversionError(f"gltf2bam timed out after {self.timeout:.0f} seconds") from exc
        except subprocess.CalledProcessError as exc:
            raise ConversionError(
                f"gltf2bam failed with exit code {exc.returncode}: {exc.stderr.strip()}"
            ) from exc

        duration = time.perf_counter() - start

        if not output_path.exists():
            raise ConversionError(f"gltf2bam did not produce output: {output_path}")

        animation_paths = sorted(animations_dir.glob("*.bam"))
        logger.info(
            "gltf2bam completed in %.2fs – %s animations generated",
            duration,
            len(animation_paths),
        )

        return ConversionResult(
            bam_path=output_path,
            animation_paths=[Path(p) for p in animation_paths],
            command=command,
            duration=duration,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )