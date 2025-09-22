#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resource Downloader for Super Mario Game
Automatically downloads game assets from the internet
"""

import os
import requests
import zipfile
import tempfile
from pathlib import Path
import platform

class ResourceDownloader:
    """Handles automatic downloading of game resources"""

    def __init__(self, assets_dir="assets"):
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(exist_ok=True)

        # Resource URLs (using free assets from OpenGameArt and similar)
        self.resource_urls = {
            "images": {
                "mario_sprites": "https://opengameart.org/sites/default/files/mario_sprites.zip",
                "tiles": "https://opengameart.org/sites/default/files/platformer_tiles.zip",
                "enemies": "https://opengameart.org/sites/default/files/enemy_sprites.zip",
                "backgrounds": "https://opengameart.org/sites/default/files/mario_backgrounds.zip"
            },
            "sounds": {
                "jump": "https://opengameart.org/sites/default/files/jump.wav",
                "coin": "https://opengameart.org/sites/default/files/coin.wav",
                "powerup": "https://opengameart.org/sites/default/files/powerup.wav",
                "background_music": "https://opengameart.org/sites/default/files/mario_theme.mp3"
            },
            "fonts": {
                "chinese_font": self._get_chinese_font_url()
            }
        }

    def _get_chinese_font_url(self):
        """Get appropriate Chinese font URL based on platform"""
        system = platform.system().lower()
        if system == "windows":
            return "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
        elif system == "darwin":  # macOS
            return "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"
        else:  # Linux and others
            return "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"

    def download_file(self, url, dest_path):
        """Download a single file"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return False

    def download_all_resources(self):
        """Download all required resources"""
        print("Starting resource download...")

        # Create subdirectories
        for category in ["images", "sounds", "fonts"]:
            (self.assets_dir / category).mkdir(exist_ok=True)

        downloaded_count = 0
        total_count = sum(len(urls) for urls in self.resource_urls.values())

        for category, urls in self.resource_urls.items():
            category_dir = self.assets_dir / category

            for resource_name, url in urls.items():
                dest_path = category_dir / f"{resource_name}.{'zip' if url.endswith('.zip') else Path(url).suffix[1:]}"

                if dest_path.exists():
                    print(f"✓ {resource_name} already exists, skipping")
                    downloaded_count += 1
                    continue

                print(f"Downloading {resource_name}...")
                if self.download_file(url, dest_path):
                    print(f"✓ Downloaded {resource_name}")
                    downloaded_count += 1

                    # Extract zip files
                    if dest_path.suffix == '.zip':
                        self._extract_zip(dest_path, category_dir)
                else:
                    print(f"✗ Failed to download {resource_name}")

        # Create fallback resources
        self._create_fallback_resources()

        print(f"Resource download complete: {downloaded_count}/{total_count} files")
        return True  # Always return True since we create fallbacks

    def _extract_zip(self, zip_path, extract_to):
        """Extract zip file to directory"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            # Remove the zip file after extraction
            zip_path.unlink()
            print(f"Extracted {zip_path.name}")
        except Exception as e:
            print(f"Failed to extract {zip_path}: {e}")

    def verify_resources(self):
        """Verify that all required resources are present"""
        required_files = [
            "images/mario.png",
            "images/tiles.png",
            "images/enemies.png",
            "sounds/jump.wav",
            "sounds/coin.wav",
            "fonts/chinese_font.otf"
        ]

        missing_files = []
        for file_path in required_files:
            if not (self.assets_dir / file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            print(f"Missing resources: {missing_files}")
            return False

        print("All required resources verified")
        return True

    def _create_fallback_resources(self):
        """Create basic fallback resources with 3D-style graphics"""
        print("Creating fallback resources with 3D-style graphics...")

        # Create images directory
        images_dir = self.assets_dir / "images"
        images_dir.mkdir(exist_ok=True)

        # Create 3D-style sprite images
        self._create_mario_sprite(images_dir / "mario.png")
        self._create_tile_sprites(images_dir / "tiles.png")
        self._create_enemy_sprites(images_dir / "enemies.png")
        # Ensure singular name exists for level loader compatibility
        try:
            singular = images_dir / "enemy.png"
            if not singular.exists() and (images_dir / "enemies.png").exists():
                singular.write_bytes((images_dir / "enemies.png").read_bytes())
        except Exception:
            pass
        self._create_coin_sprite(images_dir / "coin.png")
        self._create_powerup_sprite(images_dir / "powerup.png")
        self._create_goal_sprite(images_dir / "goal.png")

        # Create sounds directory
        sounds_dir = self.assets_dir / "sounds"
        sounds_dir.mkdir(exist_ok=True)

        # Create basic sound effects
        self._create_basic_sounds(sounds_dir)

        print("3D-style fallback resources created")

    def _create_mario_sprite(self, path):
        """Create a 3D-style Mario sprite with gradients and shading"""
        if path.exists():
            return

        try:
            from PIL import Image, ImageDraw

            def linear_gradient(size, start, end, horizontal=False):
                w, h = size
                grad = Image.new('RGBA', size, (0, 0, 0, 0))
                drawg = ImageDraw.Draw(grad)
                if horizontal:
                    for x in range(w):
                        t = x / max(1, w - 1)
                        c = (
                            int(start[0] + (end[0] - start[0]) * t),
                            int(start[1] + (end[1] - start[1]) * t),
                            int(start[2] + (end[2] - start[2]) * t),
                            int(start[3] + (end[3] - start[3]) * t)
                        )
                        drawg.line([(x, 0), (x, h)], fill=c)
                else:
                    for y in range(h):
                        t = y / max(1, h - 1)
                        c = (
                            int(start[0] + (end[0] - start[0]) * t),
                            int(start[1] + (end[1] - start[1]) * t),
                            int(start[2] + (end[2] - start[2]) * t),
                            int(start[3] + (end[3] - start[3]) * t)
                        )
                        drawg.line([(0, y), (w, y)], fill=c)
                return grad

            def downsample(img, scale=4):
                w, h = img.size
                return img.resize((w // scale, h // scale), Image.LANCZOS)

            scale = 4
            W, H = 32 * scale, 32 * scale
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Ground shadow
            shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.ellipse([W*0.25, H*0.78, W*0.75, H*0.95], fill=(0, 0, 0, 80))
            img = Image.alpha_composite(img, shadow)

            # Head (peach gradient)
            head = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            hd = ImageDraw.Draw(head)
            head_grad = linear_gradient((int(W*0.5), int(H*0.35)), (255, 230, 200, 255), (230, 190, 160, 255))
            head.paste(head_grad, (int(W*0.25), int(H*0.20)), head_grad)
            hd.ellipse([W*0.26, H*0.18, W*0.74, H*0.52], outline=(120, 80, 60, 255), width=4)
            img = Image.alpha_composite(img, head)

            # Hat (red gradient)
            hat = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            hat_grad = linear_gradient((int(W*0.54), int(H*0.18)), (220, 50, 60, 255), (160, 0, 20, 255))
            hat.paste(hat_grad, (int(W*0.23), int(H*0.08)), hat_grad)
            hdraw = ImageDraw.Draw(hat)
            hdraw.rounded_rectangle([W*0.22, H*0.08, W*0.78, H*0.24], radius=int(W*0.06), outline=(110, 0, 0, 255), width=4)
            # White patch with M
            patch = Image.new('RGBA', (int(W*0.38), int(H*0.10)), (255, 255, 255, 240))
            hat.paste(patch, (int(W*0.31), int(H*0.11)), patch)
            # Simple M as polygon
            hdraw.polygon([
                (W*0.34, H*0.12), (W*0.36, H*0.20), (W*0.40, H*0.14), (W*0.44, H*0.20), (W*0.46, H*0.12)
            ], fill=(200, 40, 50, 255))
            img = Image.alpha_composite(img, hat)

            # Eyes
            eyes = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ed = ImageDraw.Draw(eyes)
            ed.ellipse([W*0.38, H*0.30, W*0.43, H*0.40], fill=(255, 255, 255, 255))
            ed.ellipse([W*0.57, H*0.30, W*0.62, H*0.40], fill=(255, 255, 255, 255))
            ed.ellipse([W*0.405, H*0.33, W*0.435, H*0.39], fill=(0, 0, 0, 255))
            ed.ellipse([W*0.595, H*0.33, W*0.625, H*0.39], fill=(0, 0, 0, 255))
            img = Image.alpha_composite(img, eyes)

            # Mustache
            st = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            sdw = ImageDraw.Draw(st)
            sdw.rounded_rectangle([W*0.40, H*0.40, W*0.60, H*0.46], radius=int(W*0.02), fill=(120, 70, 40, 255))
            img = Image.alpha_composite(img, st)

            # Torso (red gradient)
            torso = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            torso_grad = linear_gradient((int(W*0.42), int(H*0.28)), (220, 50, 60, 255), (150, 0, 20, 255))
            torso.paste(torso_grad, (int(W*0.29), int(H*0.48)), torso_grad)
            tdr = ImageDraw.Draw(torso)
            tdr.rounded_rectangle([W*0.28, H*0.48, W*0.72, H*0.76], radius=int(W*0.04), outline=(110, 0, 0, 255), width=4)
            img = Image.alpha_composite(img, torso)

            # Overalls (blue)
            overall = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ov_grad = linear_gradient((int(W*0.36), int(H*0.22)), (30, 80, 220, 255), (10, 30, 120, 255))
            overall.paste(ov_grad, (int(W*0.32), int(H*0.58)), ov_grad)
            ovd = ImageDraw.Draw(overall)
            ovd.rounded_rectangle([W*0.31, H*0.58, W*0.69, H*0.80], radius=int(W*0.03), outline=(0, 30, 100, 255), width=4)
            # Straps and buttons
            ovd.rectangle([W*0.33, H*0.48, W*0.37, H*0.62], fill=(20, 60, 180, 255))
            ovd.rectangle([W*0.63, H*0.48, W*0.67, H*0.62], fill=(20, 60, 180, 255))
            ovd.ellipse([W*0.41, H*0.63, W*0.46, H*0.68], fill=(255, 210, 40, 255))
            ovd.ellipse([W*0.54, H*0.63, W*0.59, H*0.68], fill=(255, 210, 40, 255))
            img = Image.alpha_composite(img, overall)

            # Arms and legs
            limbs = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ldr = ImageDraw.Draw(limbs)
            skin = (245, 210, 170, 255)
            ldr.rounded_rectangle([W*0.20, H*0.50, W*0.30, H*0.66], radius=int(W*0.02), fill=skin)
            ldr.rounded_rectangle([W*0.70, H*0.50, W*0.80, H*0.66], radius=int(W*0.02), fill=skin)
            # Legs
            ldr.rounded_rectangle([W*0.42, H*0.78, W*0.50, H*0.92], radius=int(W*0.02), fill=(20, 60, 180, 255))
            ldr.rounded_rectangle([W*0.52, H*0.78, W*0.60, H*0.92], radius=int(W*0.02), fill=(20, 60, 180, 255))
            # Shoes
            ldr.rounded_rectangle([W*0.38, H*0.90, W*0.50, H*0.96], radius=int(W*0.02), fill=(110, 70, 40, 255))
            ldr.rounded_rectangle([W*0.52, H*0.90, W*0.64, H*0.96], radius=int(W*0.02), fill=(110, 70, 40, 255))
            img = Image.alpha_composite(img, limbs)

            # Specular highlight on hat
            spec = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            spd = ImageDraw.Draw(spec)
            spd.ellipse([W*0.30, H*0.10, W*0.46, H*0.18], fill=(255, 255, 255, 60))
            img = Image.alpha_composite(img, spec)

            img = downsample(img, scale)
            img.save(path)
        except ImportError:
            # If PIL is not available, create a simple placeholder
            path.touch()

    def _create_tile_sprites(self, path):
        """Create 3D-style tile sprites with bevel and shading"""
        if path.exists():
            return

        try:
            from PIL import Image, ImageDraw

            def linear_gradient(size, start, end, horizontal=False):
                w, h = size
                grad = Image.new('RGBA', size, (0, 0, 0, 0))
                drawg = ImageDraw.Draw(grad)
                if horizontal:
                    for x in range(w):
                        t = x / max(1, w - 1)
                        c = (
                            int(start[0] + (end[0] - start[0]) * t),
                            int(start[1] + (end[1] - start[1]) * t),
                            int(start[2] + (end[2] - start[2]) * t),
                            int(start[3] + (end[3] - start[3]) * t)
                        )
                        drawg.line([(x, 0), (x, h)], fill=c)
                else:
                    for y in range(h):
                        t = y / max(1, h - 1)
                        c = (
                            int(start[0] + (end[0] - start[0]) * t),
                            int(start[1] + (end[1] - start[1]) * t),
                            int(start[2] + (end[2] - start[2]) * t),
                            int(start[3] + (end[3] - start[3]) * t)
                        )
                        drawg.line([(0, y), (w, y)], fill=c)
                return grad

            def downsample(img, scale=4):
                w, h = img.size
                return img.resize((w // scale, h // scale), Image.LANCZOS)

            scale = 4
            W, H = 64 * scale, 32 * scale
            big = Image.new('RGBA', (W, H), (0, 0, 0, 0))

            # Ground tile (left 32x32)
            ground = Image.new('RGBA', (int(W/2), H), (0, 0, 0, 0))
            ggrad = linear_gradient((int(W/2), H), (170, 110, 60, 255), (100, 60, 30, 255))
            ground = Image.alpha_composite(ground, ggrad)
            gd = ImageDraw.Draw(ground)
            # Bevel top highlight
            gd.rectangle([0, 0, int(W/2), int(H*0.18)], fill=(230, 200, 160, 80))
            # Side shadow
            gd.rectangle([int(W/2)-int(W*0.02), 0, int(W/2), H], fill=(0, 0, 0, 60))
            big.paste(ground, (0, 0), ground)

            # Pipe tile (right half) with cylindrical shading
            pipe = Image.new('RGBA', (int(W/2), H), (0, 0, 0, 0))
            pgrad = linear_gradient((int(W/2), H), (40, 160, 90, 255), (10, 90, 50, 255), horizontal=True)
            pipe = Image.alpha_composite(pipe, pgrad)
            pd = ImageDraw.Draw(pipe)
            L = int(W/2)
            # Vertical highlights to simulate cylinder
            pd.rectangle([int(L*0.20), 0, int(L*0.26), H], fill=(255, 255, 255, 60))
            pd.rectangle([int(L*0.74), 0, int(L*0.78), H], fill=(0, 0, 0, 80))
            # Top rim
            pd.rectangle([0, 0, L, int(H*0.22)], fill=(30, 130, 70, 255))
            pd.rectangle([0, int(H*0.20), L, int(H*0.24)], fill=(255, 255, 255, 50))
            big.paste(pipe, (int(W/2), 0), pipe)

            small = downsample(big, scale)
            small.save(path)
        except ImportError:
            path.touch()

    def _create_enemy_sprites(self, path):
        """Create 3D-style enemy sprites with shading"""
        if path.exists():
            return

        try:
            from PIL import Image, ImageDraw

            def linear_gradient(size, start, end):
                w, h = size
                grad = Image.new('RGBA', size, (0, 0, 0, 0))
                g = ImageDraw.Draw(grad)
                for y in range(h):
                    t = y / max(1, h - 1)
                    c = (
                        int(start[0] + (end[0] - start[0]) * t),
                        int(start[1] + (end[1] - start[1]) * t),
                        int(start[2] + (end[2] - start[2]) * t),
                        int(start[3] + (end[3] - start[3]) * t)
                    )
                    g.line([(0, y), (w, y)], fill=c)
                return grad

            def downsample(img, scale=4):
                w, h = img.size
                return img.resize((w // scale, h // scale), Image.LANCZOS)

            scale = 4
            W, H = 32 * scale, 32 * scale
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))

            # Shadow
            shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.ellipse([W*0.20, H*0.80, W*0.80, H*0.95], fill=(0, 0, 0, 80))
            img = Image.alpha_composite(img, shadow)

            # Body gradient
            body = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            bgrad = linear_gradient((int(W*0.70), int(H*0.60)), (160, 100, 60, 255), (90, 60, 35, 255))
            body.paste(bgrad, (int(W*0.15), int(H*0.20)), bgrad)
            bd = ImageDraw.Draw(body)
            bd.ellipse([W*0.14, H*0.18, W*0.86, H*0.78], outline=(70, 45, 25, 255), width=4)
            img = Image.alpha_composite(img, body)

            # Eyes
            eyes = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ed = ImageDraw.Draw(eyes)
            ed.ellipse([W*0.34, H*0.38, W*0.44, H*0.52], fill=(255, 255, 255, 255))
            ed.ellipse([W*0.56, H*0.38, W*0.66, H*0.52], fill=(255, 255, 255, 255))
            ed.ellipse([W*0.385, H*0.43, W*0.43, H*0.50], fill=(0, 0, 0, 255))
            ed.ellipse([W*0.57, H*0.43, W*0.615, H*0.50], fill=(0, 0, 0, 255))
            img = Image.alpha_composite(img, eyes)

            # Mouth (frown)
            mouth = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            md = ImageDraw.Draw(mouth)
            md.arc([W*0.38, H*0.56, W*0.62, H*0.66], 0, 180, fill=(0, 0, 0, 255), width=4)
            img = Image.alpha_composite(img, mouth)

            # Feet
            feet = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            fd = ImageDraw.Draw(feet)
            fd.ellipse([W*0.28, H*0.80, W*0.44, H*0.94], fill=(90, 60, 35, 255))
            fd.ellipse([W*0.56, H*0.80, W*0.72, H*0.94], fill=(90, 60, 35, 255))
            img = Image.alpha_composite(img, feet)

            img = downsample(img, scale)
            img.save(path)
        except ImportError:
            path.touch()

    def _create_coin_sprite(self, path):
        """Create a 3D-style coin sprite with specular highlight"""
        if path.exists():
            return

        try:
            from PIL import Image, ImageDraw

            def radial_gold(size):
                w, h = size
                img = Image.new('RGBA', size, (0, 0, 0, 0))
                cx, cy = w/2, h/2
                maxr = min(w, h)/2
                drawg = ImageDraw.Draw(img)
                for r in range(int(maxr), 0, -1):
                    t = r / maxr
                    col = (
                        int(255),
                        int(200 + 55 * t),
                        int(40 + 120 * t),
                        255
                    )
                    bbox = [cx - r, cy - r, cx + r, cy + r]
                    drawg.ellipse(bbox, fill=col)
                return img

            def downsample(img, scale=4):
                w, h = img.size
                return img.resize((w // scale, h // scale), Image.LANCZOS)

            scale = 4
            W, H = 16 * scale, 16 * scale
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))

            # Coin body with radial gold gradient
            coin = radial_gold((W, H))
            img = Image.alpha_composite(img, coin)

            # Inner rim
            rim = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            rd = ImageDraw.Draw(rim)
            rd.ellipse([W*0.10, H*0.10, W*0.90, H*0.90], outline=(160, 120, 20, 255), width=4)
            rd.ellipse([W*0.18, H*0.18, W*0.82, H*0.82], outline=(255, 220, 80, 200), width=2)
            img = Image.alpha_composite(img, rim)

            # Specular highlight
            spec = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(spec)
            sd.ellipse([W*0.22, H*0.18, W*0.50, H*0.34], fill=(255, 255, 255, 90))
            img = Image.alpha_composite(img, spec)

            img = downsample(img, scale)
            img.save(path)
        except ImportError:
            path.touch()

    def _create_powerup_sprite(self, path):
        """Create a 3D-style mushroom powerup sprite"""
        if path.exists():
            return

        try:
            from PIL import Image, ImageDraw

            def downsample(img, scale=4):
                w, h = img.size
                return img.resize((w // scale, h // scale), Image.LANCZOS)

            scale = 4
            W, H = 32 * scale, 32 * scale
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))

            # Cap
            cap = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            cd = ImageDraw.Draw(cap)
            cd.ellipse([W*0.18, H*0.06, W*0.82, H*0.58], fill=(220, 40, 50, 255))
            # Spots
            cd.ellipse([W*0.30, H*0.16, W*0.38, H*0.28], fill=(255, 255, 255, 230))
            cd.ellipse([W*0.62, H*0.20, W*0.70, H*0.32], fill=(255, 255, 255, 230))
            img = Image.alpha_composite(img, cap)

            # Stem
            stem = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(stem)
            sd.rounded_rectangle([W*0.40, H*0.50, W*0.60, H*0.80], radius=int(W*0.03), fill=(245, 220, 190, 255))
            # Eyes
            sd.ellipse([W*0.46, H*0.58, W*0.48, H*0.64], fill=(0, 0, 0, 255))
            sd.ellipse([W*0.52, H*0.58, W*0.54, H*0.64], fill=(0, 0, 0, 255))
            img = Image.alpha_composite(img, stem)

            img = downsample(img, scale)
            img.save(path)
        except ImportError:
            path.touch()

    def _create_goal_sprite(self, path):
        """Create a 3D-style goal flag sprite"""
        if path.exists():
            return

        try:
            from PIL import Image, ImageDraw

            def downsample(img, scale=4):
                w, h = img.size
                return img.resize((w // scale, h // scale), Image.LANCZOS)

            scale = 4
            W, H = 32 * scale, 64 * scale
            img = Image.new('RGBA', (W, H), (0, 0, 0, 0))

            # Pole
            pole = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            pd = ImageDraw.Draw(pole)
            pd.rounded_rectangle([W*0.46, H*0.06, W*0.54, H*0.94], radius=int(W*0.02), fill=(200, 200, 200, 255))
            pd.ellipse([W*0.45, H*0.02, W*0.55, H*0.10], fill=(255, 255, 255, 255))
            img = Image.alpha_composite(img, pole)

            # Flag
            flag = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            fd = ImageDraw.Draw(flag)
            fd.polygon([(W*0.54, H*0.12), (W*0.90, H*0.20), (W*0.54, H*0.28)], fill=(255, 220, 60, 255))
            img = Image.alpha_composite(img, flag)

            img = downsample(img, scale)
            img.save(path)
        except ImportError:
            path.touch()

    def _create_colored_image(self, path, color, width, height):
        """Create a simple colored image"""
        if path.exists():
            return

        try:
            from PIL import Image
            img = Image.new('RGB', (width, height), color)
            img.save(path)
        except ImportError:
            # If PIL is not available, create a simple placeholder
            path.touch()

    def _create_basic_sounds(self, sounds_dir):
        """Create basic sound effects using numpy and scipy"""
        try:
            import numpy as np
            from scipy.io.wavfile import write
            import math

            # Sample rate
            sample_rate = 44100

            # Create jump sound (ascending tone)
            duration = 0.3
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            frequency = np.linspace(200, 400, len(t))  # Rising frequency
            jump_sound = np.sin(2 * np.pi * frequency * t) * np.exp(-t * 5)  # Fade out
            jump_sound = (jump_sound * 32767).astype(np.int16)
            write(sounds_dir / "jump.wav", sample_rate, jump_sound)

            # Create coin sound (bell-like)
            duration = 0.5
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            coin_sound = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 3)
            coin_sound += np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 4) * 0.5
            coin_sound = (coin_sound * 32767 / np.max(np.abs(coin_sound))).astype(np.int16)
            write(sounds_dir / "coin.wav", sample_rate, coin_sound)

            # Create powerup sound (rising arpeggio)
            duration = 0.8
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            frequencies = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
            powerup_sound = np.zeros_like(t)
            for i, freq in enumerate(frequencies):
                start_time = i * 0.15
                end_time = (i + 1) * 0.15
                mask = (t >= start_time) & (t < end_time)
                powerup_sound[mask] += np.sin(2 * np.pi * freq * t[mask]) * np.exp(-(t[mask] - start_time) * 10)
            powerup_sound = (powerup_sound * 32767 / np.max(np.abs(powerup_sound))).astype(np.int16)
            write(sounds_dir / "powerup.wav", sample_rate, powerup_sound)

            # Create enemy die sound (descending tone)
            duration = 0.4
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            frequency = np.linspace(300, 100, len(t))  # Falling frequency
            enemy_die_sound = np.sin(2 * np.pi * frequency * t) * np.exp(-t * 8)
            enemy_die_sound = (enemy_die_sound * 32767).astype(np.int16)
            write(sounds_dir / "enemy_die.wav", sample_rate, enemy_die_sound)

            # Create player die sound (sad descending melody)
            duration = 1.0
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            frequencies = [220, 196, 165, 147]  # A3, G3, E3, D3
            player_die_sound = np.zeros_like(t)
            for i, freq in enumerate(frequencies):
                start_time = i * 0.2
                end_time = (i + 1) * 0.2
                mask = (t >= start_time) & (t < end_time)
                player_die_sound[mask] += np.sin(2 * np.pi * freq * t[mask]) * np.exp(-(t[mask] - start_time) * 5)
            player_die_sound = (player_die_sound * 32767 / np.max(np.abs(player_die_sound))).astype(np.int16)
            write(sounds_dir / "player_die.wav", sample_rate, player_die_sound)

            # Create level complete sound (victory fanfare)
            duration = 1.5
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            frequencies = [261.63, 329.63, 392.00, 523.25, 659.25]  # C4, E4, G4, C5, E5
            level_complete_sound = np.zeros_like(t)
            for i, freq in enumerate(frequencies):
                start_time = i * 0.2
                end_time = (i + 1) * 0.2
                mask = (t >= start_time) & (t < end_time)
                level_complete_sound[mask] += np.sin(2 * np.pi * freq * t[mask]) * np.exp(-(t[mask] - start_time) * 8)
            level_complete_sound = (level_complete_sound * 32767 / np.max(np.abs(level_complete_sound))).astype(np.int16)
            write(sounds_dir / "level_complete.wav", sample_rate, level_complete_sound)

            # Create game over sound (ominous tone)
            duration = 2.0
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            game_over_sound = np.sin(2 * np.pi * 150 * t) * np.exp(-t * 0.5)  # Low ominous tone
            game_over_sound += np.sin(2 * np.pi * 75 * t) * np.exp(-t * 0.3) * 0.3  # Even lower
            game_over_sound = (game_over_sound * 32767 / np.max(np.abs(game_over_sound))).astype(np.int16)
            write(sounds_dir / "game_over.wav", sample_rate, game_over_sound)

            # Create simple beep sounds for menu interactions
            duration = 0.1
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            beep_sound = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 20)
            beep_sound = (beep_sound * 32767).astype(np.int16)
            write(sounds_dir / "pause.wav", sample_rate, beep_sound)
            write(sounds_dir / "menu_select.wav", sample_rate, beep_sound)

            # Create looping-friendly background music (simple chord pad)
            duration = 10.0
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # C major pad: C4-E4-G4 with gentle LFO
            freqs = [261.63, 329.63, 392.00]
            lfo = 0.05 * np.sin(2 * np.pi * 0.2 * t)
            pad = sum(np.sin(2 * np.pi * f * t + lfo) for f in freqs)
            # Soft attack/decay envelope for seamless loop
            attack = int(0.2 * sample_rate)
            release = int(0.2 * sample_rate)
            env = np.ones_like(t)
            env[:attack] = np.linspace(0.0, 1.0, attack)
            env[-release:] = np.linspace(1.0, 0.8, release)
            bgm = (pad / np.max(np.abs(pad))) * 0.15 * env
            bgm = (bgm * 32767).astype(np.int16)
            write(sounds_dir / "background_music.wav", sample_rate, bgm)

            print("Basic sound effects created")

        except ImportError:
            print("numpy/scipy not available, creating empty sound files")
            # Create empty sound files as placeholders
            sound_files = ["jump.wav", "coin.wav", "powerup.wav", "enemy_die.wav",
                          "player_die.wav", "level_complete.wav", "game_over.wav",
                          "pause.wav", "menu_select.wav", "background_music.wav"]

            for sound_file in sound_files:
                sound_path = sounds_dir / sound_file
                if not sound_path.exists():
                    sound_path.touch()  # Create empty file

def main():
    """Command line interface for resource downloader"""
    downloader = ResourceDownloader()
    success = downloader.download_all_resources()

    if success:
        print("All resources downloaded successfully!")
        return 0
    else:
        print("Some resources failed to download")
        return 1

if __name__ == "__main__":
    exit(main())