
# 13-core-models.md — Базовые модели (Core Models) в BotPlatform

## 1. Назначение Core Models

Core Models — это фундаментальные структуры данных платформы.  
Они описывают всё, что движки обменивают между собой через EventBus.

Эти модели:
- упрощают разработку,
- обеспечивают предсказуемость структуры данных,
- позволяют унифицировать работу разных движков,
- позволяют масштабировать систему, не меняя интерфейсы.

---

## 2. MarketSnapshot

`MarketSnapshot` — минимальная единица состояния рынка.

```python
class MarketSnapshot:
    symbol: str
    timestamp: float
    price: float
    mark_price: float
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float
    orderbook: list[OrderBookLevel] | None
    trades: list[Trade] | None
```

Используется:
- Signals Engine,
- Strategy Engine,
- Storage Layer.

---

## 3. OrderBookLevel

```python
class OrderBookLevel:
    price: float
    volume: float
```

Лёгкая структура для хранения стакана.

---

## 4. Trade

```python
class Trade:
    price: float
    quantity: float
    taker_side: str   # "buy" / "sell"
    timestamp: float
```

---

## 5. SignalSnapshot

Содержит результаты всех модулей сигналов.

```python
class SignalSnapshot:
    symbol: str
    timestamp: float
    values: dict[str, any]
```

Пример:
```json
{
  "symbol": "BTCUSDT",
  "values": {
    "rsi": 55.1,
    "ema_fast": 72401.5,
    "ema_slow": 71000,
    "cvd": -1450
  }
}
```

---

## 6. PositionSnapshot

Отражает состояние позиции на бирже.

```python
class PositionSnapshot:
    symbol: str
    side: str            # LONG / SHORT
    size: float
    entry_price: float
    leverage: float
    unrealized_pnl: float
    timestamp: float
```

Используется:
- Strategy Engine,
- StateStore,
- Execution Engine (для reduce-only).

---

## 7. StrategyContext

Передаётся в стратегию:

```python
class StrategyContext:
    symbol: str
    market: MarketSnapshot
    signals: SignalSnapshot
    position: PositionSnapshot | None
```

Стратегия видит **текущий срез информации**.

---

## 8. ActionIntent

Намерение стратегии, ещё не ордер.

```python
class ActionIntent:
    type: str            # "open", "close", "scale_in", "scale_out"
    symbol: str
    side: str            # LONG / SHORT
    size: float
    extra: dict[str, any] | None
```

Типичные действия:
- открыть позицию,
- закрыть позицию,
- увеличить объём,
- уменьшить объём,
- сделать хедж.

---

## 9. OrderIntent

Торговая заявка, отправляемая Execution Engine на биржу.

```python
class OrderIntent:
    order_type: str         # MARKET / LIMIT / STOP ...
    symbol: str
    side: str
    quantity: float
    price: float | None
    reduce_only: bool
```

ExecutionEngine гарантирует:
- корректность параметров,
- соблюдение минимальных требований биржи,
- отсутствие дублирования ордеров.

---

## 10. OrderUpdate

Обновления состояния ордера от биржи.

```python
class OrderUpdate:
    order_id: str
    symbol: str
    status: str            # filled, partial, cancelled
    filled_qty: float
    price: float
    timestamp: float
```

Используется OrderTracker и StorageLayer.

---

## 11. StateSnapshot

Снимок состояния всей платформы.

```python
class StateSnapshot:
    positions: dict[str, PositionSnapshot]
    strategies: dict[str, dict]
    timestamp: float
```

Используется:
- для восстановления после рестартов,
- для автосохранения в StorageLayer.

---

## 12. Концепция неизменяемости (immutability)

Все Core Models:
- считаются **неизменяемыми** после создания,
- обновляются только посредством создания новых версий.

Это:
- упрощает отладку,
- исключает гонки данных,
- делает поведение движков предсказуемым.

---

## 13. Роль Core Models в BotPlatform

Core Models обеспечивают:
- единый язык данных между движками,
- изоляцию бизнес-логики,
- стабильность интерфейсов,
- лёгкость тестирования,
- возможность горизонтального масштабирования,
- быструю эволюцию системы без переписывания модулей.

Core Models — фундаментальная часть платформы, вокруг которой строится весь каркас движков и событийной системы.
