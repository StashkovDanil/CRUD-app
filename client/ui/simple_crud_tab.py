from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from api_client import ApiError
from ui.widgets import RecordDialog


class SimpleCrudTab(QWidget):
    """Вкладка «список + добавить/изменить/удалить» для справочников без сложных связей."""

    def __init__(self, api_client, columns, fields, list_fn, create_fn, update_fn, delete_fn, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.columns = columns  # [(key, header), ...]
        self.fields = fields  # для RecordDialog
        self.list_fn = list_fn
        self.create_fn = create_fn
        self.update_fn = update_fn
        self.delete_fn = delete_fn
        self.rows_data: list = []

        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        self.btn_refresh = QPushButton("Обновить")
        for b in (self.btn_add, self.btn_edit, self.btn_delete, self.btn_refresh):
            btn_row.addWidget(b)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.table = QTableWidget()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in columns])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_refresh.clicked.connect(self.refresh)

        self.refresh()

    def refresh(self):
        try:
            self.rows_data = self.list_fn()
        except ApiError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            self.rows_data = []
        self._fill_table()

    def _fill_table(self):
        self.table.setRowCount(len(self.rows_data))
        for row_idx, row in enumerate(self.rows_data):
            for col_idx, (key, _) in enumerate(self.columns):
                value = row.get(key, "")
                item = QTableWidgetItem("" if value is None else str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

    def _selected_row(self):
        idx = self.table.currentRow()
        if idx < 0 or idx >= len(self.rows_data):
            return None
        return self.rows_data[idx]

    def on_add(self):
        dialog = RecordDialog("Добавить запись", self.fields, parent=self)
        if dialog.exec():
            try:
                self.create_fn(dialog.get_data())
                self.refresh()
            except ApiError as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def on_edit(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Изменение", "Выберите запись в таблице")
            return
        dialog = RecordDialog("Изменить запись", self.fields, initial=row, parent=self)
        if dialog.exec():
            try:
                self.update_fn(row["id"], dialog.get_data())
                self.refresh()
            except ApiError as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def on_delete(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Удаление", "Выберите запись в таблице")
            return
        confirm = QMessageBox.question(
            self, "Подтверждение", f"Удалить запись «{row.get('name', row.get('id'))}»?"
        )
        if confirm == QMessageBox.Yes:
            try:
                self.delete_fn(row["id"])
                self.refresh()
            except ApiError as e:
                QMessageBox.critical(self, "Ошибка", str(e))