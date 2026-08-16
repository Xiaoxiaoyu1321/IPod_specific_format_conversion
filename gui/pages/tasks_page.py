"""任务列表页：以表格展示每个文件的实时状态与进度。"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import SubtitleLabel, TableWidget

from core.models import FORMAT_SPECS, TaskStatus


class TasksPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tasksPage")
        self._rows: dict = {}  # source 路径 → 行号

        layout = QVBoxLayout(self)
        layout.addWidget(SubtitleLabel("任务列表"))
        self.table = TableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["文件", "类型", "状态", "进度", "信息"])
        self.table.setBorderVisible(True)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch)
        layout.addWidget(self.table, 1)

    def on_task(self, task) -> None:
        """根据 core 推送的任务更新表格行。"""
        key = str(task.source)
        row = self._rows.get(key)
        if row is None:
            row = self.table.rowCount()
            self._rows[key] = row
            self.table.setRowCount(row + 1)
        spec = FORMAT_SPECS[task.kind]
        cells = [
            task.name,
            f"{spec.source_exts[0]} → {spec.target_ext}",
            str(task.status),
            f"{task.progress:.0f}%",
            task.message,
        ]
        for col, text in enumerate(cells):
            item = QTableWidgetItem(text)
            if col == 2 and task.status == TaskStatus.FAILED:
                item.setForeground(Qt.red)
            elif col == 2 and task.status == TaskStatus.COMPLETED:
                item.setForeground(Qt.darkGreen)
            self.table.setItem(row, col, item)

    def clear(self) -> None:
        self._rows.clear()
        self.table.setRowCount(0)
