# Пункт C — Event Bus (Шина событий) в BotPlatform

## 1. Назначение Event Bus

Event Bus (шина событий) — центральный коммуникационный слой платформы.  
Он обеспечивает **слабую связанность** модулей:

- движков,
- стратегий,
- модулей сигналов,
- подсистем мониторинга,
- уведомлений,
- хранения состояния.

Основные задачи Event Bus:

- доставлять события между компонентами,
- позволять модулям подписываться на интересующие типы событий,
- обеспечить единый формат событий,
- быть прозрачным для расширения (локальная реализация → Redis/Kafka и т.п.).

---

## 2. Базовые принципы

1. **Все важные действия выражаются как события.**
2. **Компоненты не вызывают друг друга напрямую**, они публикуют и слушают события.
3. Каждый модуль знает:
   - какие события он публикует,
   - какие события он слушает.
4. Event Bus может иметь разные backend-реализации:
   - простая in-memory (первый этап),
   - Redis pub/sub,
   - message queue (например, NATS/Kafka) — в будущем.

---

## 3. Типы событий

Все события описываются в `core/events.py` и имеют общий базовый тип:

```python
class Event:
    type: str
    timestamp: datetime
    payload: dict
    source: str
    correlation_id: Optional[str]
```

### Основные группы событий:

1. **MarketEvent**
   - типы:
     - `market.snapshot`
   - данные:
     - `symbol`,
     - `market_snapshot` (цена, стакан, объёмы и т.п.).

2. **SignalEvent**
   - типы:
     - `signal.snapshot`
   - данные:
     - `symbol`,
     - `signal_name`,
     - `signal_snapshot`.

3. **StrategyEvent**
   - типы:
     - `strategy.decision`
   - данные:
     - `strategy_name`,
     - `symbol`,
     - `action_intents`.

4. **OrderEvent**
   - типы:
     - `order.submitted`,
     - `order.filled`,
     - `order.rejected`,
     - `order.canceled`.
   - данные:
     - `order_id`,
     - `symbol`,
     - `side`,
     - `quantity`,
     - `price`,
     - `status`.

5. **StateEvent**
   - типы:
     - `state.updated`
   - данные:
     - изменённое состояние (strategies/legs, positions и т.п.).

6. **SystemEvent**
   - типы:
     - `system.error`,
     - `system.warning`,
     - `system.heartbeat`.
   - данные:
     - модуль-источник,
     - описание ошибки или статуса.

7. **NotificationEvent**
   - типы:
     - `notification.alert`
   - данные:
     - текст сообщения,
     - уровень важности,
     - адресаты (канал/пользователь).

---

## 4. Жизненный цикл событий

Нормальный жизненный цикл:

1. Какой-либо модуль генерирует событие:
   - движок рынка формирует `MarketEvent`,
   - модуль сигналов формирует `SignalEvent`,
   - стратегия формирует `StrategyEvent`,
   - исполнение ордеров формирует `OrderEvent`.

2. Модуль публикует событие в Event Bus:
   ```python
   event_bus.publish(event)
   ```

3. Event Bus доставляет событие всем подписчикам:
   ```python
   event_bus.subscribe("signal.snapshot", callback)
   ```

4. Подписчики:
   - выполняют свою логику,
   - при необходимости порождают новые события.

---

## 5. Интерфейс Event Bus (core/event_bus.py)

Базовый интерфейс:

```python
class EventBus(Protocol):
    def publish(self, event: Event) -> None:
        ...

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        ...

    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        ...
```

Для асинхронного варианта:

```python
class AsyncEventBus(Protocol):
    async def publish(self, event: Event) -> None: ...
    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]) -> None: ...
```

---

## 6. Локальная реализация (in-memory)

На первом этапе можно использовать простую реализацию:

```python
class InMemoryEventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], None]]] = {}

    def publish(self, event: Event) -> None:
        for handler in self._subscribers.get(event.type, []):
            try:
                handler(event)
            except Exception as exc:
                # логирование ошибки
                ...

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)
```

Этого достаточно для:
- локальной разработки,
- отладки,
- написания тестов.

---

## 7. Внешняя реализация (на будущее)

Для реальной эксплуатации можно использовать:

- Redis pub/sub,
- Redis streams,
- NATS,
- Kafka,
- RabbitMQ.

В этом случае:

- `EventBus` становится обёрткой над конкретной реализацией,
- сохраняется общий интерфейс `publish/subscribe`,
- событийная модель не меняется.

Пример адаптера (условно):

```python
class RedisEventBus(EventBus):
    def __init__(self, redis_client):
        self.redis = redis_client

    def publish(self, event: Event) -> None:
        channel = f"events:{event.type}"
        self.redis.publish(channel, event.to_json())

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        # подписка на канал `events:{event_type}`
        ...
```

---

## 8. Взаимодействие модулей через Event Bus

Примеры:

### 8.1 MarketDataEngine → SignalsEngine

- `MarketDataEngine` публикует:
  - `MarketEvent(type="market.snapshot", payload={"symbol": ..., "snapshot": ...})`

- `SignalsEngine` подписан на `market.snapshot`:
  - обновляет все сигналы,
  - публикует `SignalEvent` с их результатами.

### 8.2 SignalsEngine → StrategyEngine

- `SignalsEngine` публикует:
  - `SignalEvent(type="signal.snapshot", payload={...})`

- `StrategyEngine`:
  - подписан на `signal.snapshot`,
  - комбинирует `MarketSnapshot` + `SignalSnapshot` + `PositionSnapshot`,
  - вызывает стратегии,
  - публикует `StrategyEvent`.

### 8.3 StrategyEngine → ExecutionEngine

- `StrategyEngine` публикует:
  - `StrategyEvent(type="strategy.decision", payload={"action_intents": [...]})`

- `ExecutionEngine`:
  - подписан на `strategy.decision`,
  - превращает `ActionIntent` в `OrderIntent`,
  - исполняет через `Exchange`,
  - публикует `OrderEvent`.

### 8.4 OrderEvent → Storage / Monitoring / Notifications

- Все подписаны на `order.*`:
  - `storage` пишет в журнал сделок,
  - `monitoring` обновляет UI,
  - `notifications` отправляет алерты (например, по крупным позициям).

---

## 9. Связь Event Bus и Logging

Event Bus и логирование связаны, но не смешаны:

- Event Bus → структура событий,
- Logging → текстовые/структурированные записи.

Любое событие может (и должно) сопровождаться логом.

---

## 10. Тестируемость

Event Bus позволяет:

- подменять реализацию (in-memory, mock),
- собирать все события в тестах,
- проверять поведение стратегии и движков без реальной биржи.

В тестах можно:

```python
events = []

def collector(event: Event):
    events.append(event)

event_bus.subscribe("strategy.decision", collector)
```

---

## 11. Роль Event Bus в BotPlatform

Event Bus — это:

- коммуникационная шина,
- изоляция модулей,
- возможность распределённого исполнения,
- фундамент для логирования, мониторинга, нотификаций,
- основа масштабируемости.

Без Event Bus система быстро превратится в набор жёстко связанных модулей.
