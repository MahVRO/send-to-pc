# PySide6 UI for Send-to-PC Receiver
# UI only. All logic lives in receiver.py

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QCheckBox, QComboBox
)
from PySide6.QtCore import Qt

import receiver


class SendToPCWindow(QWidget):
    # Dark theme inspired by the web sender UI
    DARK_STYLE = """
    QWidget {
        background-color: #121212;
        color: #ffffff;
        font-family: Segoe UI, Arial, sans-serif;
        font-size: 13px;
    }
    QLabel#TitleLabel {
        font-size: 22px;
        font-weight: 600;
        padding: 8px 0;
    }
    QComboBox, QCheckBox {
        background-color: #1e1e1e;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 6px 10px;
    }
    QListWidget {
        background-color: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 6px;
    }
    QListWidget::item {
        background-color: #202020;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 6px;
    }
    QListWidget::item:selected {
        background-color: #6c55ff;
    }
    QPushButton {
        background-color: #6c55ff;
        border: none;
        border-radius: 14px;
        color: white;
        font-size: 15px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #7b67ff;
    }
    QPushButton:disabled {
        background-color: #333333;
        color: #777777;
    }
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.DARK_STYLE)
        self.setWindowTitle("Send to PC")
        self.setMinimumSize(440, 620)

        self.deleted_items: set[int] = set()
        self.batches = []
        self.current_batch = None

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)

        # Title
        self.title = QLabel("Send to PC")
        self.title.setObjectName("TitleLabel")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.title)

        # Batch selector (hidden if only one batch)
        self.batch_selector = QComboBox()
        self.batch_selector.currentIndexChanged.connect(self.on_batch_changed)
        self.layout.addWidget(self.batch_selector)

        # Toggle deleted items
        self.show_deleted_checkbox = QCheckBox("Show deleted")
        self.show_deleted_checkbox.stateChanged.connect(self.refresh_list)
        self.layout.addWidget(self.show_deleted_checkbox)

        # Items list
        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget, 1)

        # Receive button
        self.receive_btn = QPushButton("Receive")
        self.receive_btn.setFixedHeight(44)
        self.receive_btn.clicked.connect(self.on_receive)
        self.layout.addWidget(self.receive_btn)

        self.load_batches()

    # =============================
    # Data loading
    # =============================

    def load_batches(self):
        self.batches = receiver.fetch_pending_batches()

        if not self.batches:
            self.list_widget.addItem("No pending batches")
            self.receive_btn.setEnabled(False)
            self.batch_selector.hide()
            return

        if len(self.batches) == 1:
            self.batch_selector.hide()
            self.current_batch = self.batches[0]
        else:
            self.batch_selector.show()
            self.batch_selector.clear()
            for i, batch in enumerate(self.batches):
                bid = batch.get("id") or batch.get("batch_id") or f"Batch {i+1}"
                self.batch_selector.addItem(bid, i)
            self.current_batch = self.batches[0]

        self.deleted_items.clear()
        self.refresh_list()

    # =============================
    # UI updates
    # =============================

    def on_batch_changed(self, index: int):
        if index < 0 or index >= len(self.batches):
            return
        self.current_batch = self.batches[index]
        self.deleted_items.clear()
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        if not self.current_batch:
            return

        items = []
        for item in self.current_batch.get("items", []):
            items.append({"type": item.get("type"), "label": item.get("type", "item")})
        for f in self.current_batch.get("files", []):
            items.append({"type": "file", "label": f.get("filename", "file")})

        show_deleted = self.show_deleted_checkbox.isChecked()

        for idx, info in enumerate(items):
            is_deleted = idx in self.deleted_items
            if is_deleted and not show_deleted:
                continue

            text = info["label"]
            if is_deleted:
                text = "[DELETED] " + text

            lw_item = QListWidgetItem(text)
            lw_item.setData(Qt.UserRole, idx)

            if is_deleted:
                lw_item.setForeground(Qt.gray)

            self.list_widget.addItem(lw_item)

        self.list_widget.itemClicked.connect(self.toggle_item)

    # =============================
    # Actions
    # =============================

    def toggle_item(self, item: QListWidgetItem):
        idx = item.data(Qt.UserRole)
        if idx in self.deleted_items:
            self.deleted_items.remove(idx)
        else:
            self.deleted_items.add(idx)
        self.refresh_list()

    def on_receive(self):
        if not self.current_batch:
            return

        receiver.accept_batch(self.current_batch, self.deleted_items)
        self.load_batches()


if __name__ == "__main__":
    app = QApplication([])
    win = SendToPCWindow()
    win.show()
    app.exec()
