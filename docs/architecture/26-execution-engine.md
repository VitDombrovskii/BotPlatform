
# 26-execution-engine-deep-dive.md — Углублённая архитектура Execution Engine

> Базовый обзор Execution Engine уже описан в `10-execution-engine.md`.  
> Этот документ дополняет его и детализирует внутреннее устройство, очереди,
> обработку ошибок, retry-логику и сериализацию ордерных потоков.

---

## 1. Роль Execution Engine в общем пайплайне

Execution Engine — последний рубеж перед биржей.  
Он отвечает за:

- приём `OrderIntent`,
- нормализацию параметров,
- постановку ордеров в очередь,
- контроль лимитов и скорости запросов,
- обработку ответов биржи (`OrderUpdate`),
- маршрутизацию update-ов обратно в Legs/стратегии.

Ключевая цель:  
**гарантировать, что каждое намерение будет либо корректно исполнено, либо корректно отвергнуто, но не потеряется и не будет выполнено дважды.**

---

## 2. Внутренняя архитектура Execution Engine

Схема:

```
                StrategyEngine
                     │
                     ▼
                OrderIntent[]
                     │
                     ▼
+------------------------------------------------------+
|                  ExecutionEngine                     |
|                                                      |
|  IntentQueue → Normalizer → RateLimiter → Sender     |
|        │              │             │         │      |
|        ▼              ▼             ▼         ▼      |
|   StateStore     ErrorHandler   RetryLogic  OrderTracker
+------------------------------------------------------+
                     │
                     ▼
                  Exchange
                     │
                     ▼
                OrderUpdate[]
```

---

## 3. IntentQueue — очередь ордеров

IntentQueue:

- принимает `OrderIntent` от StrategyEngine,
- хранит их в FIFO-порядке,
- может иметь приоритеты (по стратегии, типу, символу),
- обеспечивает backpressure, если биржа/сеть не успевает.

Типичная структура:

```python
class IntentQueue:
    def put(self, intent: OrderIntent): ...
    def get(self) -> OrderIntent: ...
    def size(self) -> int: ...
```

Может быть реализована:
- в памяти (deque, asyncio.Queue),
- в Redis (для распределённой версии),
- в Kafka/Redis Streams (для крупного масштаба).

---

## 4. Normalizer — нормализация ордеров

Задачи:

- привести размер к допустимому `lot_size`,
- привести цену к `tick_size`,
- проверить minNotional,
- скорректировать type (например, LIMIT → MARKET, если слишком далеко от цены),
- обогатить `OrderIntent` дополнительными полями (time-in-force, reduce_only).

Псевдокод:

```python
def normalize(intent: OrderIntent, rules: SymbolRules) -> OrderIntent:
    intent.size = round_to_lot(intent.size, rules.lot_size)
    if intent.price is not None:
        intent.price = round_to_tick(intent.price, rules.tick_size)
    return intent
```

---

## 5. RateLimiter — контроль частоты запросов

Биржи жёстко лимитируют API:

- X запросов в секунду,
- Y запросов в минуту,
- отдельные лимиты для ордеров.

RateLimiter:

- ставит Intent в ожидание, если лимиты близки,
- адаптивно уменьшает скорость при HTTP 429,
- может выводить систему в degraded mode.

Пример:

```python
await rate_limiter.acquire("orders")
send_order_to_exchange(...)
```

---

## 6. Sender — модуль отправки ордеров

Sender:

- принимает нормализованный `OrderIntent`,
- формирует запрос для ExchangeAdapter,
- отправляет его,
- регистрирует `client_id → local_order_id`,
- фиксирует время отправки.

---

## 7. OrderTracker — отслеживание статусов ордеров

OrderTracker хранит:

```python
class TrackedOrder:
    client_id: str
    order_id: str | None
    symbol: str
    status: str
    last_update_ts: float
    intent: OrderIntent
```

Потоки обновлений:

- через WebSocket (основной),
- через периодический REST sync (fallback).

OrderTracker:

- обновляет статус,
- вычисляет `filled_size`,
- завершает ордера в терминальных состояниях (`FILLED`, `CANCELLED`, `REJECTED`),
- при зависании ордера инициирует reconcile.

---

## 8. ErrorHandler — обработка ошибок

Типы ошибок:

1. **Сетевые ошибки** (timeout, connection reset)
2. **Биржевые ошибки** (некорректный параметр, недостаточно средств)
3. **Лимитные ошибки** (HTTP 429, ban)
4. **Логические ошибки** (конфликт параметров)

ErrorHandler решает:

- можно ли повторить запрос (`retryable = True/False`),
- нужно ли перевести Intent в статус `FAILED`,
- нужно ли поднять `system.error` / `order.error` событие.

---

## 9. RetryLogic — повторы

Политика retry:

- экспоненциальная задержка (backoff),
- лимит количества попыток,
- особое поведение при 429 (уменьшение скоростей).

Пример:

```python
for attempt in range(max_attempts):
    try:
        return await send_order()
    except RetryableError:
        await asyncio.sleep(backoff(attempt))
raise FinalError
```

Важно:  
ExecutionEngine не должен порождать дубликаты ордеров при повторных запросах —  
ключевая роль `client_id` и идемпотентности на уровне биржи (если доступно).

---

## 10. Serialize/Merge модуль (управление коллизиями)

Задача: если стратегия или Leg создают несколько Intent-ов подряд по одному и тому же символу/Leg:

- сериализовать их (исполнять по одному),
- или объединить (merge).

Примеры:

- два подряд scale-out → можно объединить в один reduce-ордер;
- open + сразу close → стратегия или RiskSystem может отменить open, вместо того чтобы исполнять обе.

Модуль merge может:

- склеивать небольшие ордера,
- заменять конфликтующие Intent-ы,
- отменять старые при появлении новых.

---

## 11. Состояние Execution Engine

Execution Engine хранит:

- активные ордера (OrderTracker),
- историю Intent-ов (для отладки),
- статистику по ошибкам,
- текущие лимиты RateLimiter.

Состояние частично сериализуется:

- для восстановления после рестарта,
- для анализа торговли.

---

## 12. Поток событий в EventBus

Execution Engine публикует:

```
order.submitted
order.acknowledged
order.filled
order.partial
order.cancelled
order.rejected
order.error
execution.latency
execution.rate_limit
```

MonitoringEngine использует эти события для alert-ов и дашбордов.

---

## 13. Поведение при сбоях

### 13.1 Потеря соединения с биржей

- переход в degraded mode,
- приостановка отправки новых ордеров,
- ретраи с увеличивающейся задержкой,
- попытка восстановить WS/REST.

### 13.2 Неподтверждённые ордера

Если ордер отправлен, но нет `order_id`:

- инициируется REST-запрос типа `GET /openOrders`,
- при обнаружении неизвестного ордера:

  - он регистрируется в OrderTracker,
  - позиция корректируется.

### 13.3 Расхождение между локальным и биржевым state

- запускается reconcile позиции (см. `24-position-model.md`),
- при критических расхождениях:
  - стратегия может быть временно отключена,
  - генерируется `risk.strategy_disabled`.

---

## 14. Масштабирование Execution Engine

### Вертикальное:

- многопоточность/asyncio-sharding по символам,
- оптимизация RateLimiter,
- параллельная обработка IntentQueue.

### Горизонтальное:

- несколько экземпляров Execution Engine,
- разделение по биржам,
- разделение по пользователям/стратегиям,
- использование распределённой очереди (Redis/Kafka).

---

## 15. Роль Execution Engine в BotPlatform (глубже)

Execution Engine — это:

- единая точка контакта с биржами,
- слой, который обеспечивает:
  - идемпотентность запроса,
  - защиту от ошибок,
  - соблюдение лимитов,
  - корректный жизненный цикл ордеров.

Он позволяет стратегиям и Legs думать только о логике,  
а не о сетевых глюках, тайм-аутах и тонкостях биржевого API.

Это «системный мозжечок» платформы — отвечает за координацию движений, не лезя в мысли.
