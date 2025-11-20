
# 09-strategy-engine.md — Strategy Engine в BotPlatform

## 1. Назначение Strategy Engine

Strategy Engine — это слой, который соединяет:
- рыночные данные (`MarketSnapshot`),
- рассчитанные сигналы (`SignalSnapshot`),
- состояние позиций (`PositionSnapshot`),
- стратегии (strategy modules),

и на их основе формирует торговые намерения (`ActionIntent`), которые потом исполняет Execution Engine.

Главная идея:
**Strategy Engine не знает о биржах напрямую**  
и **не содержит логики стратегий** — он лишь оркестрирует их выполнение.

---

## 2. Основные задачи Strategy Engine

1. Подписаться на релевантные события EventBus:
   - `market.snapshot`,
   - `signal.snapshot`,
   - `order.filled` (для обновления состояния).

2. Поддерживать текущее агрегированное состояние:
   - последнее `MarketSnapshot` по каждому символу,
   - последнее `SignalSnapshot` по каждому символу,
   - актуальные `PositionSnapshot`.

3. Передавать эти данные стратегиям:
   - вызывать `strategy.on_tick(...)` или аналогичный интерфейс.

4. Получать от стратегий `ActionIntent`:
   - вход, выход, модификация позиции,
   - вспомогательные действия (переключение режима, сброс state и т.п.).

5. Публиковать `StrategyEvent`:
   - `strategy.decision` с набором ActionIntent.

---

## 3. Компоненты Strategy Engine

```
StrategyEngine
├── StrategyRegistry
├── StateCache
├── StrategyContextBuilder
└── Publisher (EventBus)
```

### 3.1 StrategyRegistry

- отвечает за регистрацию и загрузку стратегий,
- управляет:
  - активными стратегиями,
  - конфигурацией стратегий,
  - привязкой стратегий к символам/пользователям.

Пример:
- стратегия `hedge_v2` → работает на BTCUSDT, ETHUSDT,
- стратегия `scalper_x` → только на BTCUSDT.

### 3.2 StateCache

Хранит рабочее состояние, необходимое стратегиям:

- `market_state[symbol] = last MarketSnapshot`
- `signal_state[symbol] = last SignalSnapshot`
- `positions_state[symbol] = PositionSnapshot`

### 3.3 StrategyContextBuilder

Собирает контекст для вызова стратегии:

```python
class StrategyContext:
    symbol: str
    market: MarketSnapshot
    signals: SignalSnapshot
    positions: PositionSnapshot | None
```

### 3.4 Publisher

Публикует результат работы стратегий в виде `StrategyEvent`:

```python
event.type = "strategy.decision"
event.payload = {"strategy": name, "actions": [ActionIntent, ...]}
```

---

## 4. Взаимодействие с EventBus

**Слушает:**

- `market.snapshot`
- `signal.snapshot`
- `order.filled` / `order.canceled` (для обновления позиций)
- возможно, `state.updated` (восстановление state после рестартов)

**Публикует:**

- `strategy.decision`
- `system.error` (при сбоях в логике)

---

## 5. Интерфейс стратегии

Каждая стратегия реализует единый интерфейс, например:

```python
class Strategy:
    def __init__(self, config, event_bus, storage):
        ...

    def on_tick(self, ctx: StrategyContext) -> list[ActionIntent]:
        ...
```

Где:
- `ctx` содержит весь необходимый срез состояния,
- стратегия возвращает список `ActionIntent`.

Strategy Engine:
- может вызывать несколько стратегий на один символ,
- может вызывать одну стратегию на набор символов.

---

## 6. ActionIntent — результат стратегии

`ActionIntent` — это намерение, а не ордер.

Примеры:

- `OpenPosition(symbol="BTCUSDT", side="LONG", size=0.01)`
- `ClosePosition(symbol="BTCUSDT", side="SHORT")`
- `ScaleIn(symbol="BTCUSDT", side="LONG", amount=...)`
- `ScaleOut(symbol="BTCUSDT", side="LONG", amount=...)`
- `Hedge(symbol="BTCUSDT", hedge_symbol="ETHUSDT", ratio=...)`

Execution Engine принимает эти намерения и превращает в конкретные `OrderIntent`.

---

## 7. Алгоритм работы Strategy Engine

Псевдокод:

```python
on_event(event):
    if event.type == "market.snapshot":
        state_cache.update_market(event.payload)
    if event.type == "signal.snapshot":
        state_cache.update_signals(event.payload)
    if event.type in ("order.filled", "order.canceled"):
        state_cache.update_positions(event.payload)

    for strategy in strategies:
        for symbol in strategy.symbols:
            ctx = build_context(symbol)
            if ctx is not None:
                actions = strategy.on_tick(ctx)
                if actions:
                    publish_strategy_decision(strategy.name, actions)
```

---

## 8. Масштабирование Strategy Engine

### Горизонтальное:
- один StrategyEngine на группу символов,
- один StrategyEngine на одного пользователя,
- один StrategyEngine на один тип стратегии.

### Вертикальное:
- добавление стратегий,
- усложнение логики,
- ввод дополнительных типов ActionIntent.

StrategyEngine должен быть stateless в контексте распределённости — состояние стратегий хранится в Storage, а не в самом движке.

---

## 9. Обработка ошибок

При исключении в стратегии:

- StrategyEngine:
  - логирует ошибку,
  - публикует `system.error` с деталями,
  - может временно отключить стратегию.

Важно:
- ошибка одной стратегии не должна останавливать другие,
- ошибки по одному символу не должны ломать весь движок.

---

## 10. Роль Strategy Engine в BotPlatform

Strategy Engine — это:
- исполнитель стратегий,
- координатор данных для стратегий,
- генератор торговых намерений.

Он отделяет:
- логику стратегий от движков,
- принятие решений от исполнения,
- облегчает тестирование и симуляцию.

За счёт Strategy Engine можно:
- запускать множество стратегий,
- легко добавлять новые,
- делать A/B тесты,
- реализовывать multi-strategy портфели.
