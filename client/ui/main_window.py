from PySide6.QtWidgets import QMainWindow, QTabWidget

from api_client import ApiClient
from config import API_BASE_URL
from ui.documents_tab import DocumentsTab
from ui.products_tab import ProductsTab
from ui.simple_crud_tab import SimpleCrudTab
from ui.stock_tab import StockTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Складской учёт")
        self.resize(1000, 640)

        self.api = ApiClient(API_BASE_URL)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        tabs.addTab(self._build_categories_tab(), "Категории")
        tabs.addTab(self._build_suppliers_tab(), "Поставщики")
        tabs.addTab(self._build_warehouses_tab(), "Склады")
        tabs.addTab(ProductsTab(self.api), "Товары")
        tabs.addTab(StockTab(self.api), "Остатки")
        tabs.addTab(DocumentsTab(self.api), "Документы")

    def _build_categories_tab(self):
        columns = [("id", "ID"), ("name", "Название"), ("description", "Описание")]
        fields = [
            ("name", "Название", "text", None),
            ("description", "Описание", "textarea", None),
        ]
        return SimpleCrudTab(
            self.api,
            columns,
            fields,
            list_fn=self.api.list_categories,
            create_fn=self.api.create_category,
            update_fn=self.api.update_category,
            delete_fn=self.api.delete_category,
        )

    def _build_suppliers_tab(self):
        columns = [
            ("id", "ID"),
            ("name", "Название"),
            ("contact_person", "Контакт"),
            ("phone", "Телефон"),
            ("email", "Email"),
        ]
        fields = [
            ("name", "Название", "text", None),
            ("contact_person", "Контактное лицо", "text", None),
            ("phone", "Телефон", "text", None),
            ("email", "Email", "text", None),
        ]
        return SimpleCrudTab(
            self.api,
            columns,
            fields,
            list_fn=self.api.list_suppliers,
            create_fn=self.api.create_supplier,
            update_fn=self.api.update_supplier,
            delete_fn=self.api.delete_supplier,
        )

    def _build_warehouses_tab(self):
        columns = [("id", "ID"), ("name", "Название"), ("address", "Адрес")]
        fields = [
            ("name", "Название", "text", None),
            ("address", "Адрес", "textarea", None),
        ]
        return SimpleCrudTab(
            self.api,
            columns,
            fields,
            list_fn=self.api.list_warehouses,
            create_fn=self.api.create_warehouse,
            update_fn=self.api.update_warehouse,
            delete_fn=self.api.delete_warehouse,
        )