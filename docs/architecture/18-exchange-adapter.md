
# 18-exchange-adapter.md — Exchange Adapter Layer в BotPlatform

## 1. Назначение Exchange Adapter Layer

Exchange Adapter Layer — это абстракция над конкретными биржами.  
Его задачa:

- предоставить **единый интерфейс** для работы с биржами,
- скрыть различия API,
- нормализовать данные,
- обрабатывать ошибки и особенности конкретных площадок.

Стратегии, движки и ядро **не должны знать**, Binance это или BingX, spot или futures — они работают с единым `Exchange`-интерфейсом.

---

## 2. Архитектурная схема

```
Strategy / Engines
        │
        ▼
   Exchange Interface
        │
        ▼
+----------------------+
|  Exchange Adapters   |
|  binance / bingx /   |
|  okx / bybit / ...   |
+----------------------+
        │
        ▼
   External Exchanges
```

---

## 3. Базовый интерфейс Exchange

Интерфейс задаётся в `exchanges/base.py`:

```python
class Exchange(Protocol):
    async def get_market_snapshot(self, symbol: str) -> MarketSnapshot: ...
    async def get_positions(self, symbols: list[str] | None = None) -> dict[str, PositionSnapshot]: ...

    async def place_order(self, order: OrderIntent) -> OrderUpdate: ...
    async def cancel_order(self, order_id: str, symbol: str) -> OrderUpdate: ...

    async def stream_market_data(self, symbols: list[str], callback: Callable[[MarketSnapshot], None]): ...
    async def stream_order_updates(self, callback: Callable[[OrderUpdate], None]): ...
```

Цель — минимально необходимый, но достаточный контракт.

---

## 4. Конкретные адаптеры

Структура:

```
exchanges/
├── base.py
├── binance/
│   ├── __init__.py
│   ├── adapter.py  # BinanceExchange
│   ├── models.py
│   └── utils.py
├── bingx/
│   ├── __init__.py
│   ├── adapter.py  # BingxExchange
│   ├── models.py
│   └── utils.py
└── okx/
    ├── __init__.py
    ├── adapter.py  # OkxExchange
    ├── models.py
    └── utils.py
```

Каждый `adapter.py` реализует `Exchange`:

```python
class BinanceExchange(Exchange):
    ...
```

---

## 5. Нормализация данных

Каждый адаптер отвечает за:

- приведение имен символов (например: `BTCUSDT` vs `BTC-USDT`),
- конвертацию contract size,
- работу с разными форматами orderbook/trades,
- вычисление mark price, index price (если надо),
- приведение позиций к `PositionSnapshot`.

Все различия прячутся внутри адаптера.

---

## 6. Конфигурация адаптеров

Конфиги лежат в:

```
config/connections.yaml
```

Пример:

```yaml
exchanges:
  binance:
    type: "futures"
    base_url: "https://fapi.binance.com"
    ws_url: "wss://fstream.binance.com/ws"
    api_key: "${vault:binance.api_key}"
    api_secret: "${vault:binance.api_secret}"

  bingx:
    type: "swap"
    base_url: "https://open-api.bingx.com"
    ws_url: "wss://open-api-ws.bingx.com/market"
    api_key: "${vault:bingx.api_key}"
    api_secret: "${vault:bingx.api_secret}"
```

Adapter получает конфиг на инициализации:

```python
exchange = BinanceExchange(config=cfg.exchanges["binance"])
```

---

## 7. Обработка ограничений и специфик бирж

Каждый адаптер знает:

- минимальный размер ордера,
- шаг цены (tick size),
- шаг объёма (lot size),
- максимальное количество заявок,
- особенности margin/leverage.

Перед отправкой ордера адаптер:

1. нормализует количество:
   - округление по lot size,
2. нормализует цену:
   - округление по tick size,
3. валидирует ордер относительно биржевых ограничений,
4. формирует запрос в формате конкретного API.

---

## 8. Работа с WebSocket и REST

Adapter реализует комбинированную модель:

- **REST**:
  - запросы позиций,
  - одноразовые операции (place_order, cancel_order),
  - initial sync.

- **WebSocket**:
  - поток рыночных данных,
  - поток обновлений ордеров и позиций.

Adapter должен:
- уметь переподключаться,
- восстанавливать подписки,
- синхронизировать state (WS + REST сверка).

---

## 9. Обработка ошибок

Адаптеры конвертируют ошибки в унифицированный формат:

```python
class ExchangeError(Exception):
    code: str
    message: str
    retryable: bool
```

ExecutionEngine и StrategyEngine видят только `ExchangeError`, а не коды конкретной биржи.

Примеры:
- ошибки аутентификации,
- 429 (rate limit),
- недоступность сервера,
- неверные параметры.

---

## 10. Тестирование и симуляция

Exchange Adapter Layer поддерживает:

- **MockExchange**:
  - эмуляция биржи,
  - тестирование стратегий,
  - прогон сценариев.

- **ReplayExchange**:
  - воспроизведение исторических данных,
  - симуляция исполнения ордеров,
  - обучение и отладка.

Оба реализуют тот же интерфейс `Exchange`.

---

## 11. Мульти-биржевая поддержка

BotPlatform может:

- иметь несколько активных бирж,
- запускать стратегии на нескольких одновременно,
- использовать хедж между биржами.

Exchange Layer обеспечивает:

- маршрутизацию по `exchange_id`,
- раздельную авторизацию,
- независимую обработку ошибок.

---

## 12. Модель безопасности

Adapter не хранит ключи в чистом виде:
- получает их из ConfigSystem/SecretsVault,
- держит минимально возможное время,
- может ротаировать ключи,
- не логирует секреты.

---

## 13. Роль Exchange Adapter Layer в BotPlatform

Exchange Adapter Layer:

- отделяет бизнес-логику от конкретных бирж,
- позволяет добавлять новые биржи без переписывания ядра,
- уменьшает связность,
- делает тестирование проще,
- позволяет строить сложные стратегии (hedge, cross-exchange, arb),
- является единственной точкой входа во внешний мир бирж.

Вся платформа видит биржи через единый, чистый интерфейс `Exchange`.
