
# 12-event-model.md — Модель событий (Event Model) в BotPlatform

## 1. Зачем нужна единая модель событий

События — это кровеносная система BotPlatform.  
Все движки, стратегии, адаптеры и слои хранения общаются только через события.

Единая модель событий обеспечивает:
- изоляцию модулей,
- масштабируемость,
- возможность реплея,
- возможность хранения истории,
- консистентность работы всех подсистем.

---

## 2. Базовая структура Event

```python
class Event:
    type: str            # тип события
    timestamp: float     # UNIX-время
    source: str          # модуль-источник
    correlation_id: str  # связь цепочек событий
    payload: dict        # полезные данные
```

Каждое событие обязано содержать:
- type,
- timestamp,
- source,
- payload.

Опционально:
- correlation_id (для связи цепочек событий).

---

## 3. Категории событий

Вся платформа использует 7 типов событий:

```
MarketEvent
SignalEvent
StrategyEvent
OrderEvent
StateEvent
SystemEvent
NotificationEvent
```

---

## 4. MarketEvent

Тип:
```
market.snapshot
```

Payload пример:
```json
{
  "symbol": "BTCUSDT",
  "price": 72410.5,
  "mark_price": 72412.1,
  "orderbook": [],
  "timestamp": 1710001234.23
}
```

---

## 5. SignalEvent

Тип:
```
signal.snapshot
```

Payload:
```json
{
  "symbol": "BTCUSDT",
  "values": {
      "rsi": 61.4,
      "ema_fast": 72010,
      "cvd": -1450
  }
}
```

---

## 6. StrategyEvent

Тип:
```
strategy.decision
```

Payload:
```json
{
  "strategy": "hedge_leg",
  "symbol": "BTCUSDT",
  "actions": [
    {"type": "open", "side": "long", "size": 0.01},
    {"type": "close", "side": "short", "size": 0.02}
  ]
}
```

---

## 7. OrderEvent

Используется Execution Engine и биржевыми адаптерами.

Типы:
```
order.submitted
order.filled
order.partial
order.rejected
order.cancelled
```

Payload пример:
```json
{
  "order_id": "abc123",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "price": 72400.0,
  "quantity": 0.01,
  "status": "filled"
}
```

---

## 8. StateEvent

Типы:
```
state.updated
state.snapshot
state.restored
```

Payload:
```json
{
  "positions": {"BTCUSDT": {...}},
  "strategies": {"hedge": {...}},
  "timestamp": 1710002000.12
}
```

---

## 9. SystemEvent

Типы:
```
system.error
system.warning
system.heartbeat
system.recovery
```

Payload:
```json
{
  "message": "WS connection lost",
  "severity": "high"
}
```

---

## 10. NotificationEvent

Тип:
```
notification.alert
```

Payload:
```json
{
  "text": "Position LONG BTCUSDT reached +10%",
  "priority": "info"
}
```

---

## 11. Формальные правила типов событий

1. Тип события:

```
<domain>.<action>
```

2. Payload всегда плоский (JSON-friendly).
3. События неизменяемы.
4. Любой модуль может издавать `system.error`.
5. Все события должны логироваться (если включено).

---

## 12. correlation_id — связывание событий в цепочки

Любое действие стратегии может создавать цепочку:

```
strategy.decision → order.submitted → order.filled → state.updated
```

Все события этой цепочки используют один `correlation_id`.

Это позволяет:
- отслеживать жизненный цикл действий,
- строить отчёты,
- восстанавливать состояние.

---

## 13. Жизненный цикл события

```
1. Модуль создаёт Event(...)
2. Публикует в EventBus
3. EventBus доставляет подписчикам
4. Подписчики создают новые события
5. Storage сохраняет их
6. Monitoring/Notifications обрабатывает
7. Возможен реплей через EventStore
```

---

## 14. Роль Event Model в BotPlatform

Единая модель событий обеспечивает:

- предсказуемость взаимодействия модулей,
- лёгкое масштабирование,
- гибкость при добавлении новых движков,
- тестируемость,
- возможность построения распределённой системы,
- восстановление состояния через реплей событий.

**Event Model — фундамент всей BotPlatform.**
