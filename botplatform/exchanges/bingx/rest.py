
from __future__ import annotations
import time, hmac, hashlib, requests
from typing import Dict, Any

class BingXRest:
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.key = api_key
        self.secret = api_secret.encode()
        self.url = base_url.rstrip("/")

    def _sign(self, params: Dict[str, Any]) -> str:
        qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return hmac.new(self.secret, qs.encode(), hashlib.sha256).hexdigest()

    def _headers(self):
        return {"X-BX-APIKEY": self.key, "Content-Type": "application/x-www-form-urlencoded"}

    def _request(self, method, path, params, signed):
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)
        if method == "GET":
            r = requests.get(self.url + path, headers=self._headers(), params=params)
        else:
            r = requests.post(self.url + path, headers=self._headers(), data=params)
        r.raise_for_status()
        return r.json()

    def get_price(self, symbol: str) -> float:
        data = self._request("GET", "/openApi/swap/v2/quote/price", {"symbol": symbol}, signed=False)
        price = data.get("data", {}).get("price") or data.get("price")
        return float(price)

    def place_order(self, symbol: str, side: str, qty: float, price=None, order_type="MARKET"):
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "type": order_type
        }
        if price and order_type == "LIMIT":
            params["price"] = price
        return self._request("POST", "/openApi/swap/v2/trade/order", params, signed=True)
