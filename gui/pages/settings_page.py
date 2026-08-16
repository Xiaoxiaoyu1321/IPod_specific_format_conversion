"""设置页：ffmpeg、线程数、缓存与增强功能开关。"""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    BodyLabel, CardWidget, FluentIcon as FIF, InfoBar, InfoBarPosition,
    LineEdit, PrimaryPushButton, PushButton, SpinBox, SubtitleLabel,
    SwitchButton, ToolButton,
)

from core.config import AppConfig
from core.ffmpeg import FFmpegError, FFmpegLocator


class SettingsPage(QWidget):
    saved = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self._init_ui(config)

    def _init_ui(self, config: AppConfig) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # ffmpeg 卡片
        ff_card = CardWidget(self)
        ff_layout = QGridLayout(ff_card)
        ff_layout.setContentsMargins(24, 20, 24, 20)
        ff_layout.setVerticalSpacing(14)

        ff_layout.addWidget(BodyLabel("ffmpeg 目录", self), 0, 0)
        self.ffmpeg_edit = LineEdit(self)
        self.ffmpeg_edit.setText(config.ffmpeg_dir)
        self.ffmpeg_edit.setPlaceholderText("留空则依次查找 bin/ffmpeg 与系统 PATH")
        browse = ToolButton(FIF.FOLDER, self)
        browse.clicked.connect(self._pick_ffmpeg)
        detect = PushButton("检测", self)
        detect.clicked.connect(self._detect_ffmpeg)
        ff_layout.addWidget(self.ffmpeg_edit, 0, 1)
        ff_layout.addWidget(browse, 0, 2)
        ff_layout.addWidget(detect, 0, 3)

        ff_layout.addWidget(BodyLabel("ffmpeg 下载地址", self), 1, 0)
        self.url_edit = LineEdit(self)
        self.url_edit.setText(config.ffmpeg_download_url)
        ff_layout.addWidget(self.url_edit, 1, 1, 1, 3)

        layout.addWidget(ff_card)

        # 通用设置卡片
        common_card = CardWidget(self)
        common_layout = QGridLayout(common_card)
        common_layout.setContentsMargins(24, 20, 24, 20)
        common_layout.setVerticalSpacing(14)

        common_layout.addWidget(BodyLabel("ffmpeg 线程数", self), 0, 0)
        self.thread_spin = SpinBox(self)
        self.thread_spin.setRange(1, 16)
        self.thread_spin.setValue(config.threads)
        common_layout.addWidget(self.thread_spin, 0, 1)

        self.keep_temp_switch = SwitchButton("保留中间 WAV 缓存", self)
        self.keep_temp_switch.setChecked(config.keep_temp)
        common_layout.addWidget(self.keep_temp_switch, 1, 0, 1, 2)

        self.keep_pic_switch = SwitchButton("保留封面缓存", self)
        self.keep_pic_switch.setChecked(config.keep_temp_pic)
        common_layout.addWidget(self.keep_pic_switch, 2, 0, 1, 2)

        self.cover_switch = SwitchButton("自动下载专辑封面", self)
        self.cover_switch.setChecked(config.download_cover)
        common_layout.addWidget(self.cover_switch, 3, 0, 1, 2)

        self.lyrics_switch = SwitchButton("自动下载歌词（.lrc）", self)
        self.lyrics_switch.setChecked(config.download_lyrics)
        common_layout.addWidget(self.lyrics_switch, 4, 0, 1, 2)

        layout.addWidget(common_card)

        # 保存按钮
        btn_row = QHBoxLayout()
        save_btn = PrimaryPushButton(FIF.SAVE, "保存设置", self)
        save_btn.clicked.connect(self.saved)
        btn_row.addWidget(save_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)
        layout.addStretch(1)

    def _pick_ffmpeg(self) -> None:
        start = self.ffmpeg_edit.text().strip() or None
        path = QFileDialog.getExistingDirectory(self, "选择 ffmpeg 所在目录", start)
        if path:
            self.ffmpeg_edit.setText(path)

    def _detect_ffmpeg(self) -> None:
        cfg = AppConfig()
        self.collect_into(cfg)
        try:
            ffmpeg, ffprobe = FFmpegLocator(cfg).locate()
            InfoBar.success(
                "检测成功",
                f"ffmpeg: {ffmpeg}\nffprobe: {ffprobe}",
                parent=self, position=InfoBarPosition.TOP_RIGHT, duration=5000,
            )
        except FFmpegError as exc:
            InfoBar.error(
                "未找到 ffmpeg", str(exc),
                parent=self, position=InfoBarPosition.TOP_RIGHT, duration=6000,
            )

    def collect_into(self, cfg: AppConfig) -> None:
        cfg.ffmpeg_dir = self.ffmpeg_edit.text().strip()
        cfg.ffmpeg_download_url = self.url_edit.text().strip()
        cfg.threads = self.thread_spin.value()
        cfg.keep_temp = self.keep_temp_switch.isChecked()
        cfg.keep_temp_pic = self.keep_pic_switch.isChecked()
        cfg.download_cover = self.cover_switch.isChecked()
        cfg.download_lyrics = self.lyrics_switch.isChecked()
