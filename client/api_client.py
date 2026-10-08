import requests


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class ApiClient:
    """Тонкая обёртка над REST API склада (контракт см. api/openapi.yaml)."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            resp = self.session.request(method, url, timeout=10, **kwargs)
        except requests.RequestException as exc:
            raise ApiError(0, f"Ошибка соединения с сервером: {exc}") from exc
        if not resp.ok:
            try:
                detail = resp.json().get("detail", resp.text)
            except ValueError:
                detail = resp.text
            raise ApiError(resp.status_code, str(detail))
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ------------------------------------------------------------- Категории
    def list_categories(self):
        return self._request("GET", "/categories")

    def create_category(self, data: dict):
        return self._request("POST", "/categories", json=data)

    def update_category(self, id_: int, data: dict):
        return self._request("PUT", f"/categories/{id_}", json=data)

    def delete_category(self, id_: int):
        return self._request("DELETE", f"/categories/{id_}")

    # ------------------------------------------------------------ Поставщики
    def list_suppliers(self):
        return self._request("GET", "/suppliers")

    def create_supplier(self, data: dict):
        return self._request("POST", "/suppliers", json=data)

    def update_supplier(self, id_: int, data: dict):
        return self._request("PUT", f"/suppliers/{id_}", json=data)

    def delete_supplier(self, id_: int):
        return self._request("DELETE", f"/suppliers/{id_}")

    # -------------------------------------------------------------- Склады
    def list_warehouses(self):
        return self._request("GET", "/warehouses")

    def create_warehouse(self, data: dict):
        return self._request("POST", "/warehouses", json=data)

    def update_warehouse(self, id_: int, data: dict):
        return self._request("PUT", f"/warehouses/{id_}", json=data)

    def delete_warehouse(self, id_: int):
        return self._request("DELETE", f"/warehouses/{id_}")

    # -------------------------------------------------------------- Товары
    def list_products(self, category_id: int | None = None):
        params = {"category_id": category_id} if category_id else {}
        return self._request("GET", "/products", params=params)

    def create_product(self, data: dict):
        return self._request("POST", "/products", json=data)

    def update_product(self, id_: int, data: dict):
        return self._request("PUT", f"/products/{id_}", json=data)

    def delete_product(self, id_: int):
        return self._request("DELETE", f"/products/{id_}")

    # ------------------------------------------------------------- Остатки
    def list_stock(self, warehouse_id: int | None = None):
        params = {"warehouse_id": warehouse_id} if warehouse_id else {}
        return self._request("GET", "/stock", params=params)

    def adjust_stock(self, id_: int, quantity: float):
        return self._request("PATCH", f"/stock/{id_}", json={"quantity": quantity})

    # ------------------------------------------------------------ Документы
    def list_documents(self):
        return self._request("GET", "/documents")

    def get_document(self, id_: int):
        return self._request("GET", f"/documents/{id_}")

    def create_document(self, data: dict):
        return self._request("POST", "/documents", json=data)

    def delete_document(self, id_: int):
        return self._request("DELETE", f"/documents/{id_}")

    def post_document(self, id_: int):
        return self._request("POST", f"/documents/{id_}/post")