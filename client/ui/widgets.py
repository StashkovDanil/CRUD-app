from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
)


class RecordDialog(QDialog):
    """
    Универсальное диалоговое окно создания/редактирования записи.

    fields: [(key, label, widget_type, extra), ...]
        widget_type: "text" | "textarea" | "number" | "combo"
        extra: для "number" — (min, max, decimals); для "combo" — [(value, text), ...]
    """

    def __init__(self, title: str, fields: list, initial: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(360)
        self._widgets: dict = {}
        initial = initial or {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        for key, label, wtype, extra in fields:
            if wtype == "text":
                w = QLineEdit(str(initial.get(key, "") or ""))
            elif wtype == "textarea":
                w = QTextEdit(str(initial.get(key, "") or ""))
                w.setFixedHeight(70)
            elif wtype == "number":
                w = QDoubleSpinBox()
                min_v, max_v, decimals = extra
                w.setRange(min_v, max_v)
                w.setDecimals(decimals)
                w.setValue(float(initial.get(key, 0) or 0))
            elif wtype == "combo":
                w = QComboBox()
                for value, text in extra:
                    w.addItem(text, value)
                if initial.get(key) is not None:
                    idx = w.findData(initial[key])
                    if idx >= 0:
                        w.setCurrentIndex(idx)
            else:
                raise ValueError(f"Неизвестный тип поля: {wtype}")
            self._widgets[key] = (wtype, w)
            form.addRow(label, w)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict:
        data = {}
        for key, (wtype, w) in self._widgets.items():
            if wtype == "text":
                text = w.text().strip()
                data[key] = text or None
            elif wtype == "textarea":
                text = w.toPlainText().strip()
                data[key] = text or None
            elif wtype == "number":
                data[key] = w.value()
            elif wtype == "combo":
                data[key] = w.currentData()
        return data