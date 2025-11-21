from __future__ import annotations

import time
import hmac
import hashlib
from typing import Dict, Any, Optional

import requests


class BingXRest:
    """Простой REST-клиент для BingX.

    Это не полный охват API, а минимальный набор:
    - получение цены
    - размещение ордера
    - (опционально) получение позиций

    Важно: конечные точки и параметры необходимо сверить с
    официальной документацией BingX перед использованием в бою.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://open-api.bingx.com",
        recv_window: int = 5000,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window

    # ------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> str:
        """Подпись запроса HMAC SHA256.

        Точный формат подписи зависит от API BingX.
        Здесь используется стандартный подход:
        - сортируем параметры по ключу
        - конкатенируем в query string
        - считаем HMAC-SHA256 по секретному ключу
        """
        items = sorted(params.items())
        payload = "&".join(f"{k}={v}" for k, v in items)
        return hmac.new(self.api_secret, payload.encode(), hashlib.sha256).hexdigest()

    def _headers(self) -> Dict[str, str]:
        return {
            "X-BX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        url = self.base_url + path
        params = params.copy() if params else {}

        if signed:
            params.setdefault("recvWindow", self.recv_window)
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        if method == "GET":
            resp = requests.get(url, headers=self._headers(), params=params, timeout=10)
        else:
            resp = requests.post(url, headers=self._headers(), data=params, timeout=10)

        resp.raise_for_status()
        data = resp.json()
        return data

    # ------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------

    def get_price(self, symbol: str) -> float:
        """Получить последнюю рыночную цену инструмента.

        Эндпоинт и формат ответа нужно сверить с документацией BingX.
        Здесь предполагается структура вида:
        { "data": { "price": "12345.67" }, ... }
        """
        path = "/openApi/swap/v2/quote/price"
        params = {"symbol": symbol}
        data = self._request("GET", path, params=params, signed=False)
        # Защитный парсинг
        price_str = (
            data.get("data", {}).get("price")
            or data.get("price")
            or data.get("lastPrice")
        )
        if price_str is None:
            raise RuntimeError(f"Unexpected price response from BingX: {data}")
        return float(price_str)

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "MARKET",
        position_side: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Разместить ордер на BingX.

        Параметры и эндпоинт примерны и должны быть адаптированы под
        конкретный режим торговли (spot / swap / futures).
        """
        path = "/openApi/swap/v2/trade/order"
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if price is not None and order_type == "LIMIT":
            params["price"] = price
        if position_side:
            params["positionSide"] = position_side
        return self._request("POST", path, params=params, signed=True)
