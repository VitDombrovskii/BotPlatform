
# 25-intents-and-order-model.md — Intents & Order Model в BotPlatform

## 1. Назначение Intents & Order Model

Intents & Order Model — это мост между логикой Legs и фактическими ордерами биржи.

Он обеспечивает:
- разделение действий (ActionIntent) и биржевых ордеров (OrderIntent),
- универсальный торговый пайплайн,
- независимость стратегий от конкретной биржи,
- детерминированное исполнение,
- тестируемость и воспроизводимость.

Намерение — это ещё не ордер.  
Это декларация того, *что Leg хочет сделать*.

---

## 2. Общий поток исполнения

```
Leg → ActionIntent → StrategyEngine → ExecutionEngine
     → OrderIntent → ExchangeAdapter → Exchange
     → OrderUpdate → ExecutionEngine → Leg
```

Этот цикл — основа всей торговой логики платформы.

---

## 3. ActionIntent — высокоуровневые намерения Legs

ActionIntent создаёт Leg.

Примеры:

```
open (открыть позицию)
close (закрыть позицию)
scale_in (увеличить позицию)
scale_out (уменьшить позицию)
bubble_entry (открытие пузырька)
bubble_exit  (закрытие пузырька)
```

Формат:

```python
class ActionIntent(BaseModel):
    action: str               # open / close / scale_in / bubble_entry ...
    side: str                 # LONG / SHORT
    size: float | None = None
    price: float | None = None
    context: dict | None = None
```

ActionIntent описывает *чего хочет Leg*, но ExecutionEngine ещё должен решить:

- как нормализовать размер,
- какой тип ордера использовать,
- какие лимиты применить,
- не нарушает ли Intent риск-правила.

---

## 4. OrderIntent — ордер, готовый к отправке на биржу

OrderIntent — результат переработки ActionIntent.

```python
class OrderIntent(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    type: Literal["MARKET", "LIMIT"]
    size: float
    price: float | None
    client_id: str
    source: str            # long_leg / short_leg / strategy_name
    context: dict | None
```

OrderIntent — это уже почти биржевой ордер, но ещё не адаптированный под конкретную биржу.

---

## 5. Execution Pipeline

### 5.1 Создание ActionIntent в Leg
Leg принимает решение на основе:
- StrategyContext,
- своего состояния,
- bubble/scale контроллеров.

### 5.2 StrategyEngine собирает Intent-ы всех Legs

### 5.3 ExecutionEngine выполняет валидацию

Проверяются:
- размер,
- риск-лимиты (max_size),
- конфликтующие действия между Legs,
- фильтры GlobalRiskController.

### 5.4 ExecutionEngine создаёт OrderIntent
С добавлением:
- client_id,
- дополнительного контекста,
- правильного типа ордера.

### 5.5 ExchangeAdapter превращает OrderIntent в биржевой запрос
Адаптер нормализует:
- количество по lot_size,
- цену по tick_size,
- параметры запроса.

### 5.6 Биржа принимает ордер

### 5.7 Биржа отправляет OrderUpdate

### 5.8 ExecutionEngine маршрутизирует update в нужный Leg

---

## 6. OrderUpdate — финальный ответ биржи

```python
class OrderUpdate(BaseModel):
    order_id: str
    client_id: str
    symbol: str
    status: Literal["NEW", "PARTIAL", "FILLED", "CANCELLED", "REJECTED"]
    filled_size: float
    remaining_size: float
    avg_fill_price: float | None
    timestamp: int
    raw: dict
```

Leg использует update чтобы:
- обновить размер позиции,
- пересчитать entry_price (при scale),
- обновить реализованный PnL,
- завершить bubble,
- корректировать scale_state.

---

## 7. Уникальность client_id

Каждый Intent получает уникальный client_id:

```
leg.<strategy>.<long|short>.<uuid4>
```

Зачем:

- сопоставить OrderUpdate и Intent,
- отслеживать дубликаты,
- исключить повторное исполнение,
- анализировать историю.

---

## 8. Edge Cases — сложные сценарии

### 8.1 Потерянный update
ExecutionEngine обнаруживает несоответствие размера позиции → запускает reconcile.

### 8.2 Дубликаты Intent-ов
Если Leg отправил ActionIntent два раза:
→ ExecutionEngine обнаружит одинаковый client_id и откажет второму Intent.

### 8.3 Partial fill
Leg обновляет entry_price с учётом avg_fill_price.

### 8.4 Intent отменён стратегией
ExecutionEngine отправляет cancel-order.

---

## 9. События EventBus

ExecutionEngine публикует ключевые события:

```
intent.created
intent.validated
intent.translated
intent.sent
order.placed
order.filled
order.cancelled
order.rejected
order.error
```

MonitoringEngine отслеживает всю цепочку.

---

## 10. Почему Intent Model обязательна?

Intent Model:

- разделяет бизнес-логику и инфраструктуру,
- делает Legs независимыми,
- обеспечивает многоуровневый контроль,
- позволяет иметь несколько стратегий,
- даёт прозрачный trading pipeline,
- позволяет тестировать торговлю без биржи,
- делает систему предсказуемой.

Без Intent Model Legs пришлось бы писать под каждую биржу отдельно,  
что превратило бы код в хаос.

С Intent Model BotPlatform становится модульной, стабильной и масштабируемой.

