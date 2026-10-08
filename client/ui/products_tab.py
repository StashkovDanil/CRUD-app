from PySide6.QtWidgets import QMessageBox

from api_client import ApiError
from ui.simple_crud_tab import SimpleCrudTab


class ProductsTab(SimpleCrudTab):
    """Товары: список показывает название категории; форма — выбор категории (combo)."""

    def __init__(self, api_client, parent=None):
        columns = [
            ("id", "ID"),
            ("sku", "Артикул"),
            ("name", "Название"),
            ("category_name", "Категория"),
            ("unit", "Ед."),
            ("price", "Цена"),
        ]
        super().__init__(
            api_client,
            columns,
            fields=[],  # формируется динамически в _build_fields()
            list_fn=lambda: api_client.list_products(),
            create_fn=api_client.create_product,
            update_fn=api_client.update_product,
            delete_fn=api_client.delete_product,
            parent=parent,
        )

    def _build_fields(self):
        try:
            categories = self.api.list_categories()
        except ApiError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            categories = []
        options = [(c["id"], c["name"]) for c in categories]
        return [
            ("sku", "Артикул", "text", None),
            ("name", "Название", "text", None),
            ("category_id", "Категория", "combo", options),
            ("unit", "Ед. измерения (по умолчанию «шт»)", "text", None),
            ("price", "Цена", "number", (0, 10_000_000, 2)),
            ("description", "Описание", "textarea", None),
        ]

    def on_add(self):
        self.fields = self._build_fields()
        super().on_add()

    def on_edit(self):
        self.fields = self._build_fields()
        super().on_edit()