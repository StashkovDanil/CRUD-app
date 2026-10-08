from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from api_client import ApiError

TYPE_LABELS = {"IN": "Приход", "OUT": "Расход"}
STATUS_LABELS = {"DRAFT": "Черновик", "POSTED": "Проведён"}


class NewDocumentDialog(QDialog):
    """Создание документа: шапка + позиции — связь documents<->products (M:M)."""

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.setWindowTitle("Новый документ")
        self.setMinimumSize(520, 460)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.doc_number_edit = QLineEdit()
        form.addRow("Номер документа", self.doc_number_edit)

        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItem("Приход", "IN")
        self.doc_type_combo.addItem("Расход", "OUT")
        form.addRow("Тип документа", self.doc_type_combo)

        self.warehouse_combo = QComboBox()
        for w in self._safe(api_client.list_warehouses):
            self.warehouse_combo.addItem(w["name"], w["id"])
        form.addRow("Склад", self.warehouse_combo)

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("— не указан —", None)
        for s in self._safe(api_client.list_suppliers):
            self.supplier_combo.addItem(s["name"], s["id"])
        form.addRow("Поставщик", self.supplier_combo)

        self.comment_edit = QTextEdit()
        self.comment_edit.setFixedHeight(50)
        form.addRow("Комментарий", self.comment_edit)

        self.products = self._safe(api_client.list_products)

        layout.addWidget(QLabel("Позиции документа:"))
        item_btns = QHBoxLayout()
        self.btn_add_item = QPushButton("Добавить позицию")
        self.btn_remove_item = QPushButton("Удалить позицию")
        item_btns.addWidget(self.btn_add_item)
        item_btns.addWidget(self.btn_remove_item)
        item_btns.addStretch()
        layout.addLayout(item_btns)

        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(["Товар", "Количество", "Цена"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.items_table)

        self.btn_add_item.clicked.connect(self.add_item_row)
        self.btn_remove_item.clicked.connect(self.remove_item_row)
        self.add_item_row()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _safe(self, fn):
        try:
            return fn()
        except ApiError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return []

    def add_item_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        product_combo = QComboBox()
        for p in self.products:
            product_combo.addItem(f"{p['sku']} — {p['name']}", p["id"])
        self.items_table.setCellWidget(row, 0, product_combo)

        qty_spin = QDoubleSpinBox()
        qty_spin.setRange(0.001, 1_000_000)
        qty_spin.setDecimals(3)
        qty_spin.setValue(1)
        self.items_table.setCellWidget(row, 1, qty_spin)

        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 10_000_000)
        price_spin.setDecimals(2)
        self.items_table.setCellWidget(row, 2, price_spin)

    def remove_item_row(self):
        row = self.items_table.currentRow()
        if row >= 0:
            self.items_table.removeRow(row)

    def on_accept(self):
        if not self.doc_number_edit.text().strip():
            QMessageBox.warning(self, "Проверка", "Укажите номер документа")
            return
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Проверка", "Добавьте хотя бы одну позицию")
            return
        self.accept()

    def get_data(self) -> dict:
        items = []
        for row in range(self.items_table.rowCount()):
            product_combo = self.items_table.cellWidget(row, 0)
            qty_spin = self.items_table.cellWidget(row, 1)
            price_spin = self.items_table.cellWidget(row, 2)
            items.append(
                {
                    "product_id": product_combo.currentData(),
                    "quantity": qty_spin.value(),
                    "price": price_spin.value(),
                }
            )
        return {
            "doc_number": self.doc_number_edit.text().strip(),
            "doc_type": self.doc_type_combo.currentData(),
            "warehouse_id": self.warehouse_combo.currentData(),
            "supplier_id": self.supplier_combo.currentData(),
            "comment": self.comment_edit.toPlainText().strip() or None,
            "items": items,
        }


class DocumentsTab(QWidget):
    """Документы прихода/расхода. Проведение документа изменяет остатки на складе."""

    COLUMNS = [
        ("doc_number", "Номер"),
        ("doc_type", "Тип"),
        ("warehouse_name", "Склад"),
        ("supplier_name", "Поставщик"),
        ("status", "Статус"),
        ("created_at", "Создан"),
    ]

    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.rows_data: list = []

        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Создать документ")
        self.btn_view = QPushButton("Просмотр позиций")
        self.btn_post = QPushButton("Провести")
        self.btn_delete = QPushButton("Удалить черновик")
        self.btn_refresh = QPushButton("Обновить")
        for b in (self.btn_add, self.btn_view, self.btn_post, self.btn_delete, self.btn_refresh):
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels([c[1] for c in self.COLUMNS])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self.on_add)
        self.btn_view.clicked.connect(self.on_view)
        self.btn_post.clicked.connect(self.on_post)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_refresh.clicked.connect(self.refresh)

        self.refresh()

    def refresh(self):
        try:
            self.rows_data = self.api.list_documents()
        except ApiError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.rows_data = []
        self.table.setRowCount(len(self.rows_data))
        for row_idx, row in enumerate(self.rows_data):
            for col_idx, (key, _) in enumerate(self.COLUMNS):
                value = row.get(key, "")
                if key == "doc_type":
                    value = TYPE_LABELS.get(value, value)
                if key == "status":
                    value = STATUS_LABELS.get(value, value)
                item = QTableWidgetItem("" if value is None else str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

    def _selected(self):
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self.rows_data):
            return None
        return self.rows_data[idx]

    def on_add(self):
        dialog = NewDocumentDialog(self.api, parent=self)
        if dialog.exec():
            try:
                self.api.create_document(dialog.get_data())
                self.refresh()
            except ApiError as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def on_view(self):
        row = self._selected()
        if row is None:
            QMessageBox.information(self, "Просмотр", "Выберите документ в таблице")
            return
        try:
            detail = self.api.get_document(row["id"])
        except ApiError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        lines = [f"{i['product_name']}: {i['quantity']} x {i['price']}" for i in detail["items"]]
        QMessageBox.information(
            self,
            f"Документ №{detail['doc_number']}",
            "\n".join(lines) if lines else "Нет позиций",
        )

    def on_post(self):
        row = self._selected()
        if row is None:
            QMessageBox.information(self, "Проведение", "Выберите документ в таблице")
            return
        confirm = QMessageBox.question(self, "Подтверждение", f"Провести документ №{row['doc_number']}?")
        if confirm == QMessageBox.Yes:
            try:
                self.api.post_document(row["id"])
                self.refresh()
            except ApiError as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def on_delete(self):
        row = self._selected()
        if row is None:
            QMessageBox.information(self, "Удаление", "Выберите документ в таблице")
            return
        confirm = QMessageBox.question(self, "Подтверждение", f"Удалить черновик №{row['doc_number']}?")
        if confirm == QMessageBox.Yes:
            try:
                self.api.delete_document(row["id"])
                self.refresh()
            except ApiError as e:
                QMessageBox.critical(self, "Ошибка", str(e))