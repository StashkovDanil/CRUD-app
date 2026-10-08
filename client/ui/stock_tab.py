from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from api_client import ApiError


class StockTab(QWidget):
    """Остатки товаров по складам — связь products<->warehouses (M:M) с атрибутом quantity."""

    COLUMNS = [
        ("product_name", "Товар"),
        ("warehouse_name", "Склад"),
        ("quantity", "Количество"),
        ("updated_at", "Обновлено"),
    ]

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.rows_data: list = []

        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.btn_adjust = QPushButton("Скорректировать остаток")
        self.btn_refresh = QPushButton("Обновить")
        btn_row.addWidget(self.btn_adjust)
        btn_row.addWidget(self.btn_refresh)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([c[1] for c in self.COLUMNS])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_adjust.clicked.connect(self.on_adjust)
        self.btn_refresh.clicked.connect(self.refresh)

        self.refresh()

    def refresh(self):
        try:
            self.rows_data = self.api.list_stock()
        except ApiError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.rows_data = []
        self.table.setRowCount(len(self.rows_data))
        for row_idx, row in enumerate(self.rows_data):
            for col_idx, (key, _) in enumerate(self.COLUMNS):
                value = row.get(key, "")
                item = QTableWidgetItem("" if value is None else str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

    def on_adjust(self):
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self.rows_data):
            QMessageBox.information(self, "Корректировка", "Выберите строку остатка")
            return
        row = self.rows_data[idx]
        value, ok = QInputDialog.getDouble(
            self,
            "Корректировка остатка (инвентаризация)",
            f"Новое количество «{row['product_name']}» на складе «{row['warehouse_name']}»:",
            float(row["quantity"]),
            0,
            1_000_000,
            3,
        )
        if ok:
            try:
                self.api.adjust_stock(row["id"], value)
                self.refresh()
            except ApiError as e:
                QMessageBox.critical(self, "Ошибка", str(e))