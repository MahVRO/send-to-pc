# PySide6 UI for Send-to-PC Receiver
# - Batch dropdown (only when >1 batch)
# - Card-style list with explicit delete/restore button per item
# - Show-deleted toggle (shows deleted at 50% opacity with ✓)
# - Receive routes deleted items to received/deleted via receiver.accept_batch(...)
# - Network timeouts/outages never crash the UI (Receive doubles as Retry)

from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QCheckBox,
    QComboBox,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import receiver


# -----------------------------
# UI widgets
# -----------------------------

class ItemCard(QFrame):
    def __init__(self, idx: int, title: str, subtitle: str, badge: str, deleted: bool, on_toggle):
        super().__init__()
        self.idx = idx
        self._on_toggle = on_toggle

        self.setObjectName("ItemCard")
        self.setProperty("deleted", deleted)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)

        self.badge = QLabel(badge)
        self.badge.setObjectName("Badge")
        self.badge.setAlignment(Qt.AlignCenter)
        top.addWidget(self.badge)

        self.title = QLabel(title)
        self.title.setObjectName("ItemTitle")
        self.title.setTextInteractionFlags(Qt.TextSelectableByMouse)
        top.addWidget(self.title, 1)

        left.addLayout(top)

        self.subtitle = QLabel(subtitle)
        self.subtitle.setObjectName("ItemSubtitle")
        self.subtitle.setWordWrap(True)
        self.subtitle.setTextInteractionFlags(Qt.TextSelectableByMouse)
        left.addWidget(self.subtitle)

        root.addLayout(left, 1)

        self.btn = QPushButton("✓" if deleted else "✕")
        self.btn.setObjectName("ToggleBtn")
        self.btn.setFixedSize(28, 28)
        self.btn.clicked.connect(self._toggle)
        root.addWidget(self.btn)

        self.set_deleted(deleted)

    def _toggle(self):
        self._on_toggle(self.idx)

    def set_deleted(self, deleted: bool):
        self.setProperty("deleted", deleted)
        self.btn.setText("✓" if deleted else "✕")
        # Force QSS refresh
        self.style().unpolish(self)
        self.style().polish(self)


# -----------------------------
# Main window
# -----------------------------

class SendToPCWindow(QWidget):
    STYLE = """
    QWidget {
        background-color: #0f0f12;
        color: #ffffff;
        font-family: Segoe UI, Arial, sans-serif;
        font-size: 13px;
    }

    QLabel#TitleLabel {
        font-size: 22px;
        font-weight: 650;
        padding: 6px 0;
    }

    QLabel#StatusLabel {
        color: rgba(255,255,255,0.75);
        padding: 0 2px 2px 2px;
    }

    QComboBox, QCheckBox {
        background-color: #191a1f;
        border: 1px solid #2a2b35;
        border-radius: 10px;
        padding: 8px 10px;
    }

    QListWidget {
        background-color: #14151a;
        border: 1px solid #2a2b35;
        border-radius: 14px;
        padding: 8px;
        outline: none;
    }

    QFrame#ItemCard {
        background-color: #1b1c22;
        border: 1px solid #2a2b35;
        border-radius: 14px;
    }

    QFrame#ItemCard[deleted="true"] {
        background-color: rgba(27,28,34,0.65);
        border: 1px solid rgba(42,43,53,0.55);
    }

    QLabel#Badge {
        background-color: #6c55ff;
        color: white;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 999px;
        min-width: 44px;
    }

    QLabel#ItemTitle {
        font-size: 14px;
        font-weight: 650;
    }

    QLabel#ItemSubtitle {
        color: rgba(255,255,255,0.70);
        font-size: 12px;
    }

    QPushButton#PrimaryBtn {
        background-color: #6c55ff;
        border: none;
        border-radius: 14px;
        color: white;
        font-size: 15px;
        font-weight: 700;
        padding: 10px;
    }

    QPushButton#PrimaryBtn:hover {
        background-color: #7b67ff;
    }

    QPushButton#ToggleBtn {
        background-color: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        font-weight: 900;
    }
    """
    STYLE = """
    QWidget {
        background-color: #0f0f12;
        color: #ffffff;
        font-family: Segoe UI, Arial, sans-serif;
        font-size: 13px;
    }

    QLabel#TitleLabel {
        font-size: 22px;
        font-weight: 650;
        padding: 6px 0;
    }

    QLabel#StatusLabel {
        color: rgba(255,255,255,0.75);
        padding: 0 2px 2px 2px;
    }

    QComboBox, QCheckBox {
        background-color: #191a1f;
        border: 1px solid #2a2b35;
        border-radius: 10px;
        padding: 8px 10px;
    }

    QListWidget {
        background-color: #14151a;
        border: 1px solid #2a2b35;
        border-radius: 14px;
        padding: 8px;
        outline: none;
    }

    QFrame#ItemCard {
        background-color: #1b1c22;
        border: 1px solid #2a2b35;
        border-radius: 14px;
    }

    QFrame#ItemCard[deleted="true"] {
        background-color: rgba(27,28,34,0.65);
        border: 1px solid rgba(42,43,53,0.55);
    }

    QLabel#Badge {
        background-color: #6c55ff;
        color: white;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 999px;
        min-width: 44px;
    }

    QFrame#ItemCard[deleted="true"] QLabel#Badge {
        background-color: rgba(108,85,255,0.55);
    }

    QLabel#ItemTitle {
        font-size: 14px;
        font-weight: 650;
    }

    QLabel#ItemSubtitle {
        color: rgba(255,255,255,0.72);
        font-size: 12px;
    }

    QPushButton#PrimaryBtn {
        background-color: #6c55ff;
        border: none;
        border-radius: 14px;
        color: white;
        font-size: 15px;
        font-weight: 700;
        padding: 10px;
    }

    QPushButton#PrimaryBtn:hover {
        background-color: #7b67ff;
    }

    QPushButton#PrimaryBtn:disabled {
        background-color: #2a2b35;
        color: rgba(255,255,255,0.35);
    }

    QPushButton#ToggleBtn {
        background-color: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 10px;
        font-weight: 900;
    }

    QPushButton#ToggleBtn:hover {
        background-color: rgba(255,255,255,0.10);
    }

    QFrame#ItemCard[deleted="true"] QPushButton#ToggleBtn {
        background-color: rgba(108,85,255,0.10);
        border: 1px solid rgba(108,85,255,0.25);
    }
    """

    def __init__(self):
        super().__init__()
        self.setStyleSheet(self.STYLE)
        self.setWindowTitle("Send to PC")
        self.setMinimumSize(460, 680)

        self.batches: list[dict] = []
        self.current_batch: dict | None = None
        self.flat_items: list[dict] = []  # [{idx, kind, title, subtitle, badge}]
        self.deleted_indexes: set[int] = set()

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Send to PC")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        self.status = QLabel("")
        self.status.setObjectName("StatusLabel")
        self.status.setAlignment(Qt.AlignCenter)
        root.addWidget(self.status)

        self.batch_selector = QComboBox()
        self.batch_selector.currentIndexChanged.connect(self.on_batch_changed)
        root.addWidget(self.batch_selector)

        toggles = QHBoxLayout()
        toggles.setSpacing(10)

        self.show_deleted = QCheckBox("Show deleted")
        self.show_deleted.stateChanged.connect(self.refresh_list)
        toggles.addWidget(self.show_deleted)

        toggles.addStretch(1)

        root.addLayout(toggles)

        self.list = QListWidget()
        self.list.setSpacing(8)
        root.addWidget(self.list, 1)

        self.receive_btn = QPushButton("Receive")
        self.receive_btn.setObjectName("PrimaryBtn")
        self.receive_btn.setFixedHeight(48)
        self.receive_btn.clicked.connect(self.on_receive)
        root.addWidget(self.receive_btn)

        self.load_batches()

    # -----------------------------
    # Data + shaping
    # -----------------------------

    def _set_status(self, text: str):
        self.status.setText(text)

    def _fmt_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.0f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _set_status(self, text: str):
        self.status.setText(text)

    def _shape_current_batch(self):
        self.flat_items = []
        if not self.current_batch:
            return

        items = self.current_batch.get("items", [])
        files = self.current_batch.get("files", [])

        # Items (text/code) – skip empty text/code
        for i, it in enumerate(items):
            kind = (it.get("type") or "item").lower()
            content = it.get("content")
            if content is None or not str(content).strip():
                continue  # do not show empty items

            badge = "TEXT" if kind == "text" else "CODE" if kind == "code" else kind.upper()
            title = "Text message" if kind == "text" else "Code snippet" if kind == "code" else "Item"

            preview = str(content).strip().replace("\r", "")
            if len(preview) > 160:
                preview = preview[:160] + "…"

            self.flat_items.append({
                "idx": i,
                "badge": badge,
                "title": title,
                "subtitle": preview,
            })

        # Files
        base = len(items)
        for j, f in enumerate(files):
            idx = base + j
            filename = f.get("filename") or "file"
            size = f.get("size")
            size_txt = self._fmt_size(size) if isinstance(size, int) else ""
            subtitle = f"File • {size_txt}" if size_txt else "File"

            self.flat_items.append({
                "idx": idx,
                "badge": "FILE",
                "title": filename,
            "subtitle": subtitle,
        })

    # -----------------------------
    # Loading
    # -----------------------------

    def load_batches(self):
        self.receive_btn.setEnabled(False)
        self.batch_selector.hide()
        self.list.clear()
        self._set_status("Connecting…")
        self.list.addItem("Connecting to server…")

        try:
            self.batches = receiver.fetch_pending_batches()
        except Exception:
            self.current_batch = None
            self.flat_items = []
            self.deleted_indexes.clear()
            self.list.clear()
            self._set_status("Server unavailable")
            self.list.addItem("Server unavailable. Click Receive to retry.")
            self.receive_btn.setEnabled(True)
            return

        self.deleted_indexes.clear()

        if not self.batches:
            self.current_batch = None
            self.flat_items = []
            self.list.clear()
            self._set_status("No pending batches")
            self.list.addItem("No pending batches")
            self.receive_btn.setEnabled(False)
            return

        self.batch_selector.clear()
        if len(self.batches) == 1:
            self.current_batch = self.batches[0]
            self.batch_selector.hide()
        else:
            self.batch_selector.show()
            for i, b in enumerate(self.batches):
                bid = b.get("id") or b.get("batch_id") or f"Batch {i+1}"
                self.batch_selector.addItem(bid, i)
            self.current_batch = self.batches[0]

        self.receive_btn.setEnabled(True)
        self._shape_current_batch()
        self.refresh_list()
        # Never crash the UI on network problems
        self.receive_btn.setEnabled(False)
        self.batch_selector.hide()
        self.list.clear()
        self._set_status("Connecting…")
        self.list.addItem("Connecting to server…")

        try:
            self.batches = receiver.fetch_pending_batches()
        except Exception:
            self.current_batch = None
            self.flat_items = []
            self.deleted_indexes.clear()
            self.list.clear()
            self._set_status("Server unavailable")
            self.list.addItem("Server unavailable. Click Receive to retry.")
            self.receive_btn.setEnabled(True)
            return

        self.deleted_indexes.clear()

        if not self.batches:
            self.current_batch = None
            self.flat_items = []
            self.list.clear()
            self._set_status("No pending batches")
            self.list.addItem("No pending batches")
            self.receive_btn.setEnabled(False)
            return

        # Batch selector only if >1
        self.batch_selector.clear()
        if len(self.batches) == 1:
            self.current_batch = self.batches[0]
            self.batch_selector.hide()
        else:
            self.batch_selector.show()
            for i, b in enumerate(self.batches):
                bid = b.get("id") or b.get("batch_id") or f"Batch {i+1}"
                self.batch_selector.addItem(bid, i)
            self.current_batch = self.batches[0]

        self.receive_btn.setEnabled(True)
        self._shape_current_batch()
        self.refresh_list()

    def on_batch_changed(self, idx: int):
        if idx < 0 or idx >= len(self.batches):
            return
        self.current_batch = self.batches[idx]
        self.deleted_indexes.clear()
        self._shape_current_batch()
        self.refresh_list()

    # -----------------------------
    # Rendering
    # -----------------------------

    def refresh_list(self):
        self.list.clear()

        if not self.current_batch:
            return

        total = len(self.flat_items)
        deleted = len(self.deleted_indexes)
        self._set_status(f"Items: {total} • Deleted: {deleted}")

        show_deleted = self.show_deleted.isChecked()

        visible = 0
        for info in self.flat_items:
            idx = info["idx"]
            is_deleted = idx in self.deleted_indexes
            if is_deleted and not show_deleted:
                continue

            card = ItemCard(
                idx=idx,
                title=info["title"],
                subtitle=info["subtitle"],
                badge=info["badge"],
                deleted=is_deleted,
                on_toggle=self.toggle_item,
            )

            row_item = QListWidgetItem()
            row_item.setFlags(row_item.flags() & ~Qt.ItemIsSelectable)
            row_item.setSizeHint(card.sizeHint())
            self.list.addItem(row_item)
            self.list.setItemWidget(row_item, card)
            visible += 1

        if visible == 0:
            self.list.addItem("(No visible items)")

    # -----------------------------
    # Actions
    # -----------------------------

    def toggle_item(self, idx: int):
        if idx in self.deleted_indexes:
            self.deleted_indexes.remove(idx)
        else:
            self.deleted_indexes.add(idx)
        self.refresh_list()

    def on_receive(self):
        if not self.current_batch:
            self.load_batches()
            return

        self.receive_btn.setEnabled(False)
        self._set_status("Receiving…")
        self.list.clear()
        self.list.addItem("Receiving…")

        try:
            receiver.accept_batch(self.current_batch, self.deleted_indexes)
        except Exception:
            self._set_status("Receive failed")
            self.list.clear()
            self.list.addItem("Error while receiving. Click Receive to retry.")
            self.receive_btn.setEnabled(True)
            self.current_batch = None
            return

        self.load_batches()


if __name__ == "__main__":
    app = QApplication([])
    app.setFont(QFont("Segoe UI", 10))
    w = SendToPCWindow()
    w.show()
    app.exec()
