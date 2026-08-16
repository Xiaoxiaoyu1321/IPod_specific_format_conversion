"""首页：目录选择、转换类型、开始/停止与实时日志。"""
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    BodyLabel, CardWidget, CheckBox, FluentIcon as FIF, LineEdit,
    PrimaryPushButton, ProgressBar, PushButton, SubtitleLabel,
    TextEdit, ToolButton,
)

from core.config import AppConfig
from core.models import FORMAT_SPECS, FormatKind, TaskStatus


class HomePage(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")
        self._running = False
        self._init_ui(config)

    # ---- UI 构建 ----
    def _init_ui(self, config: AppConfig) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # 目录卡片
        dir_card = CardWidget(self)
        dir_layout = QGridLayout(dir_card)
        dir_layout.setContentsMargins(24, 20, 24, 20)
        dir_layout.setVerticalSpacing(14)
        dir_layout.setHorizontalSpacing(12)

        self.input_edit = self._make_dir_row(dir_layout, 0, "输入目录",
                                             config.input_dir, self._pick_input)
        self.output_edit = self._make_dir_row(dir_layout, 1, "输出目录",
                                              config.output_dir, self._pick_output)
        self.qq_edit = self._make_dir_row(dir_layout, 2, "QQ音乐目录（解密用）",
                                          config.qq_music_dir, self._pick_qq)
        layout.addWidget(dir_card)

        # 转换类型卡片
        kind_card = CardWidget(self)
        kind_layout = QVBoxLayout(kind_card)
        kind_layout.setContentsMargins(24, 20, 24, 20)
        kind_layout.addWidget(SubtitleLabel("转换类型"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        self.kind_checks: dict = {}
        selected = set(config.kinds)
        for idx, (kind, spec) in enumerate(FORMAT_SPECS.items()):
            cb = CheckBox(spec.label, self)
            cb.setChecked(kind.value in selected)
            self.kind_checks[kind] = cb
            grid.addWidget(cb, idx // 2, idx % 2)
        kind_layout.addLayout(grid)
        layout.addWidget(kind_card)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.start_btn = PrimaryPushButton(FIF.PLAY, "开始转换", self)
        self.stop_btn = PushButton(FIF.CANCEL, "停止", self)
        self.stop_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_requested)
        self.stop_btn.clicked.connect(self.stop_requested)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # 进度
        prog_row = QHBoxLayout()
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label = BodyLabel("就绪", self)
        prog_row.addWidget(self.progress_bar, 1)
        prog_row.addWidget(self.status_label)
        layout.addLayout(prog_row)

        # 日志
        self.log_view = TextEdit(self)
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view, 1)

    def _make_dir_row(self, grid: QGridLayout, row: int, label: str,
                      value: str, picker) -> LineEdit:
        grid.addWidget(BodyLabel(label, self), row, 0, Qt.AlignLeft)
        edit = LineEdit(self)
        edit.setText(value)
        edit.setPlaceholderText("请选择目录…")
        btn = ToolButton(FIF.FOLDER, self)
        btn.setToolTip("浏览…")
        btn.clicked.connect(picker)
        grid.addWidget(edit, row, 1)
        grid.addWidget(btn, row, 2)
        return edit

    # ---- 目录选择 ----
    def _pick_input(self) -> None:
        self._pick_into(self.input_edit)

    def _pick_output(self) -> None:
        self._pick_into(self.output_edit)

    def _pick_qq(self) -> None:
        self._pick_into(self.qq_edit)

    def _pick_into(self, edit: LineEdit) -> None:
        start = edit.text().strip() or None
        path = QFileDialog.getExistingDirectory(self, "选择目录", start)
        if path:
            edit.setText(path)

    # ---- 配置采集 ----
    def collect_into(self, cfg: AppConfig) -> None:
        cfg.input_dir = self.input_edit.text().strip()
        cfg.output_dir = self.output_edit.text().strip()
        cfg.qq_music_dir = self.qq_edit.text().strip()
        cfg.kinds = [k.value for k, cb in self.kind_checks.items() if cb.isChecked()]

    # ---- 运行状态 ----
    def set_running(self, running: bool) -> None:
        self._running = running
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)
        if not running:
            self.status_label.setText("就绪")

    @property
    def running(self) -> bool:
        return self._running

    # ---- 信号槽 ----
    def append_log(self, line: str) -> None:
        self.log_view.append(line)

    def on_task(self, task) -> None:
        """更新首页进度条（展示最近一个任务的进度）。"""
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                           TaskStatus.SKIPPED):
            self.progress_bar.setValue(100 if task.status == TaskStatus.COMPLETED
                                       else 0)
        else:
            self.progress_bar.setValue(int(task.progress))
        self.status_label.setText(f"{task.name} — {task.status}")
