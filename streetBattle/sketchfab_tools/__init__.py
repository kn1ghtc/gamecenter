"""Utility package for managing Sketchfab authentication and downloads."""

from .cookie_session import (
    SketchfabCookieSession,
    SketchfabCookieError,
    SketchfabAuthError,
    SketchfabRateLimitError,
)
from .downloader import SketchfabSequentialDownloader, SketchfabDownloadSummary
from .conversion import Gltf2BamConverter, ConversionError, ConversionResult

__all__ = [
    "SketchfabCookieSession",
    "SketchfabCookieError",
    "SketchfabAuthError",
    "SketchfabRateLimitError",
    "SketchfabSequentialDownloader",
    "SketchfabDownloadSummary",
    "Gltf2BamConverter",
    "ConversionError",
    "ConversionResult",
]
