from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from .config import SettingsManager


class GameLauncher:
    """Interactive front-end allowing players to choose between 2.5D and 3D modes."""

    def __init__(self, settings_manager: Optional[SettingsManager] = None) -> None:
        self.settings_manager = settings_manager or SettingsManager()
        preferred = self.settings_manager.get("preferred_version", "3d")
        self.root = tk.Tk()
        self.root.title("StreetBattle Launcher")
        self.root.geometry("420x260")
        self.root.resizable(False, False)
        self.root.configure(bg="#111623")

        self.selected_version = tk.StringVar(value=preferred)
        remember = bool(self.settings_manager.get("remember_last_version", True))
        self.remember_var = tk.BooleanVar(value=remember)

        self._build_layout()

    def _build_layout(self) -> None:
        heading = ttk.Label(
            self.root,
            text="StreetBattle 游戏启动器",
            font=("Segoe UI", 16, "bold"),
        )
        heading.pack(pady=(20, 8))

        subheading = ttk.Label(
            self.root,
            text="选择要启动的版本。配置可在界面保存，也可直接编辑 config/settings.json。",
            wraplength=360,
            justify="center",
        )
        subheading.pack(pady=(0, 20))

        radio_frame = ttk.Frame(self.root)
        radio_frame.pack(pady=4)

        ttk.Radiobutton(
            radio_frame,
            text="3D 版本（Panda3D）",
            value="3d",
            variable=self.selected_version,
        ).grid(row=0, column=0, padx=12, pady=4, sticky="w")

        ttk.Radiobutton(
            radio_frame,
            text="2.5D 精灵版（Pygame）",
            value="2.5d",
            variable=self.selected_version,
        ).grid(row=1, column=0, padx=12, pady=4, sticky="w")

        remember_checkbox = ttk.Checkbutton(
            self.root,
            text="记住选择 (写入 config/settings.json)",
            variable=self.remember_var,
        )
        remember_checkbox.pack(pady=(6, 14))

        buttons = ttk.Frame(self.root)
        buttons.pack(pady=(10, 0))

        ttk.Button(buttons, text="启动游戏", command=self._on_launch).grid(row=0, column=0, padx=6)
        ttk.Button(buttons, text="打开配置文件", command=self._open_config_file).grid(row=0, column=1, padx=6)
        ttk.Button(buttons, text="重新载入配置", command=self._reload_settings).grid(row=0, column=2, padx=6)

        footer = ttk.Label(
            self.root,
            text="提示：启动 2.5D 将开启独立窗口，关闭可返回本界面重新选择。",
            wraplength=380,
            justify="center",
        )
        footer.pack(pady=(18, 6))

    def _persist_selection(self) -> None:
        if self.remember_var.get():
            self.settings_manager.set("preferred_version", self.selected_version.get(), persist=False)
        self.settings_manager.set("remember_last_version", self.remember_var.get(), persist=False)
        self.settings_manager.save()

    def _on_launch(self) -> None:
        version = self.selected_version.get()
        self._persist_selection()
        self.root.destroy()
        try:
            if version == "2.5d":
                self._launch_sprite_mode()
            else:
                self._launch_3d_mode()
        except Exception as exc:  # pragma: no cover - runtime safety for launcher
            messagebox.showerror("启动失败", f"启动 {version} 模式时出现问题：\n{exc}")

    def _open_config_file(self) -> None:
        path = self.settings_manager.path
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])

    def _reload_settings(self) -> None:
        self.settings_manager.refresh()
        self.selected_version.set(self.settings_manager.get("preferred_version", "3d"))
        self.remember_var.set(bool(self.settings_manager.get("remember_last_version", True)))
        messagebox.showinfo("已重新载入", "配置文件中的设置已重新载入。")

    def _launch_3d_mode(self) -> None:
        from . import main as streetbattle_main

        app = streetbattle_main.StreetBattleGame(settings_manager=self.settings_manager)
        app.run()

    def _launch_sprite_mode(self) -> None:
        from .twod5.game import SpriteBattleGame

        game = SpriteBattleGame(settings_manager=self.settings_manager)
        game.run()

    def run(self) -> None:
        self.root.mainloop()


def launch() -> None:
    launcher = GameLauncher()
    launcher.run()


__all__ = ["GameLauncher", "launch"]
