
# 10-execution-engine.md — Execution Engine в BotPlatform

## 1. Назначение Execution Engine

Execution Engine — подсистема, которая принимает торговые намерения (`ActionIntent`) от Strategy Engine и превращает их в реальные биржевые заявки (`OrderIntent`).  
Это единственный слой платформы, который напрямую общается с биржевыми API.

Основной поток:
**ActionIntent → OrderIntent → ExchangeAdapter → OrderEvent**

---

## 2. Основные обязанности Execution Engine

1. Обработка `strategy.decision`.
2. Преобразование ActionIntent → OrderIntent.
3. Отправка ордеров на биржу.
4. Трекинг статусов ордеров.
5. Управление скоростью запросов и ограничениями биржи.
6. Публикация событий исполнения:
   - `order.submitted`
   - `order.filled`
   - `order.partial`
   - `order.rejected`
   - `order.cancelled`

---

## 3. Компоненты Execution Engine

```
ExecutionEngine
├── IntentRouter
├── OrderBuilder
├── RateLimiter
├── ExchangeAdapter
├── OrderTracker
└── Publisher (EventBus)
```

### 3.1 IntentRouter  
Определяет обработчик для каждого типа ActionIntent.

### 3.2 OrderBuilder  
Строит корректный `OrderIntent`:
- учитывает шаг цены,
- минимальный шаг объёма,
- reduce-only,
- post-only,
- стоп-условия.

### 3.3 RateLimiter  
Не допускает превышения лимитов биржи:
- запросов в секунду,
- активаций ордеров,
- burst limits.

### 3.4 ExchangeAdapter  
Единственный модуль, знающий особенности API:
- формат ордера,
- авторизация,
- обработка ошибок,
- очистка ответов.

### 3.5 OrderTracker  
Поддерживает статус активных ордеров:
- ожидание исполнения,
- проверка WS/REST обновлений,
- закрытие/отмена.

### 3.6 Publisher  
Публикует `order.*` события обратно в EventBus.

---

## 4. Трансформация ActionIntent → OrderIntent

Пример:

ActionIntent:
```
OpenPosition(side=LONG, size=0.05)
```

ExecutionEngine выполняет:

1. Валидацию.
2. Создание `OrderIntent`:
```
OrderIntent(
  type="MARKET",
  side="BUY",
  quantity=0.05,
  reduce_only=False
)
```
3. Отправку через адаптер.
4. Публикацию `order.submitted`.
5. Трекинг до фактического исполнения.
6. Публикацию `order.filled`.

---

## 5. Взаимодействие с EventBus

**Слушает:**
```
strategy.decision
```

**Публикует:**
```
order.submitted
order.filled
order.partial
order.rejected
order.cancelled
system.error
```

Execution Engine является конечной точкой принятия решений стратегий.

---

## 6. Алгоритм работы Execution Engine

Псевдокод:

```python
on_event(strategy.decision):
    for action in event.payload["actions"]:
        order = OrderBuilder.from_action(action)
        rate_limiter.wait_if_needed()
        response = exchange.send_order(order)
        publish(order.submitted)

on_event(exchange.ws_update):
    order_tracker.update(msg)
    if msg.status == "filled":
        publish(order.filled)
    if msg.status == "partial":
        publish(order.partial)
    if msg.status == "canceled":
        publish(order.cancelled)
```

---

## 7. Обработка ошибок и отказоустойчивость

Execution Engine обязан:
- повторять запросы при временных сбоях,
- корректно реагировать на ошибки 429,
- проверять расхождения между WS и REST,
- не допускать двойной отправки ордера,
- очищать зависшие ордера,
- публиковать `system.error` с деталями.

Ошибки Execution Engine не должны ломать стратегию или Market Engine.

---

## 8. Масштабирование Execution Engine

### Горизонтальное:
- один движок на биржу,
- один движок на пользователя,
- один движок на группу стратегий,
- один движок на символ.

### Вертикальное:
- оптимизация rate limiting,
- многопоточность адаптеров,
- обработка сотен ордеров/сек.

---

## 9. Роль Execution Engine в BotPlatform

Execution Engine — это контур исполнения в реальном мире:

- он воплощает решения стратегий,
- обеспечивает точность и безопасность торговли,
- сглаживает особенности бирж и API,
- отвечает за корректный жизненный цикл всех ордеров.

Стратегия принимает решение.  
Execution Engine делает торговлю реальностью.
