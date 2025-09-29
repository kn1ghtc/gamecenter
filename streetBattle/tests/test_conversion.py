from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from gamecenter.streetBattle.sketchfab_tools.conversion import (
    ConversionError,
    Gltf2BamConverter,
)


def _write_minimal_gltf(path: Path) -> None:
    payload = {
        "asset": {"version": "2.0"},
        "scenes": [0],
        "nodes": [{"mesh": 0}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_converter_runs_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    gltf = tmp_path / "hero.gltf"
    output = tmp_path / "hero.bam"
    animations_dir = tmp_path / "anim"
    _write_minimal_gltf(gltf)

    def fake_run(command, cwd, check, capture_output, text, timeout, env):  # noqa: ANN001
        output.write_bytes(b"bam")
        animations_dir.mkdir(parents=True, exist_ok=True)
        (animations_dir / "Idle.bam").write_bytes(b"idle")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)  # type: ignore[arg-type]

    converter = Gltf2BamConverter(command=["gltf2bam"], timeout=10.0)
    result = converter.convert(
        source_path=gltf,
        output_path=output,
        animations_dir=animations_dir,
    )

    assert result.bam_path == output
    assert output.exists()
    assert any(path.name == "Idle.bam" for path in result.animation_paths)
    assert all(path.exists() for path in result.animation_paths)


def test_converter_raises_on_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    gltf = tmp_path / "hero.gltf"
    animations_dir = tmp_path / "anim"
    _write_minimal_gltf(gltf)

    def fake_run(command, cwd, check, capture_output, text, timeout, env):  # noqa: ANN001
        raise subprocess.CalledProcessError(1, command, stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)  # type: ignore[arg-type]

    converter = Gltf2BamConverter(command=["gltf2bam"])

    with pytest.raises(ConversionError) as exc:
        converter.convert(
            source_path=gltf,
            output_path=tmp_path / "hero.bam",
            animations_dir=animations_dir,
        )

    assert "exit code" in str(exc.value)