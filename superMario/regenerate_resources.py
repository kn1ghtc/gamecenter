#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate 3D-style resources"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.downloader import ResourceDownloader

if __name__ == "__main__":
    rd = ResourceDownloader()
    rd._create_fallback_resources()
    print("✓ 3D-style resources regenerated successfully")
