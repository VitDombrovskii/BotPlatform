
# 24-position-model.md — Position Model в BotPlatform

## 1. Назначение Position Model

Position Model — это единая унифицированная модель позиции,
которая используется всеми движками, Legs, стратегиями и адаптерами бирж.

Она обеспечивает:
- корректный расчёт средней цены,
- точный учёт realized/unrealized PnL,
- синхронизацию фактического состояния с биржей,
- хранение позиции между перезапусками,
- поддержку multi-leg стратегий,
- атомарность и неизменяемость снапшотов.

Position Model — фундаментальный элемент платформы.

---

## 2. Архитектура Position Model

```
PositionSnapshot
├── symbol         (BTC-USDT)
├── side           (LONG / SHORT)
├── size           (float)
├── entry_price    (float)
├── realized_pnl   (float)
├── unrealized_pnl (float)
└── leverage       (optional)
```

PositionSnapshot всегда:
- иммутабельный,
- создаётся движком или получен из биржи,
- описывает состояние позиции в один момент времени.

---

## 3. PositionSnapshot — структура

```python
class PositionSnapshot(BaseModel):
    symbol: str
    side: Literal["LONG", "SHORT"]
    size: float
    entry_price: float
    realized_pnl: float
    unrealized_pnl: float
    leverage: float | None = None
```

---

## 4. Расчёт средней цены позиции

Средняя цена пересчитывается при scale-in:

```
new_entry_price =
   (old_entry_price * old_size + fill_price * added_size)
   / (old_size + added_size)
```

Если scale-out → средняя цена НЕ меняется.

---

## 5. Расчёт PnL

### 5.1 Unrealized PnL

```
LONG:
  pnl = (mark_price - entry_price) * size

SHORT:
  pnl = (entry_price - mark_price) * size
```

### 5.2 Realized PnL

Рассчитывается только при закрытии части позиции:

```
closed_size = old_size - new_size

realized += (fill_price - entry_price) * closed_size (LONG)
realized += (entry_price - fill_price) * closed_size (SHORT)
```

---

## 6. Atomic Snapshot

Все снапшоты позиций в платформе атомарны:

- MARKET ENGINE обновляет позицию целиком,
- STRATEGY ENGINE читает снапшот целиком,
- LEGS получают immutable копию,
- STORAGE сохраняет снимок полностью.

Нельзя изменять PositionSnapshot — только пересоздавать.

---

## 7. Синхронизация позиции с биржей (Reconcile)

Reconcile выполняется:

- при старте,
- после network errors,
- после ордерных разрывов,
- по расписанию.

Алгоритм:

```
1. Получить позицию с биржи (exchange.get_positions)
2. Сравнить со stored_state
3. Если расхождение:
       update PositionSnapshot
       скорректировать LegState
       отправить event position.reconciled
```

---

## 8. Position Model и Legs

Каждая Leg получает свою проекцию позиции:

```
full_position → split by side → leg_position
```

Пример:

Если биржа даёт aggregated (net) позицию:

```
size > 0  → LONG leg
size < 0  → SHORT leg
size = 0  → обе empty
```

Если hedge-strategy использует независимые legs — PositionModel является источником истины.

---

## 9. Ошибки и edge cases

### 9.1 Неполное обновление
Если биржа прислала нелогичные значения размера:
→ выполняется emergency reconcile.

### 9.2 Разрыв между fill и update
ExecutionEngine делает merge:

```
expected_size vs actual_size
```

Если есть несовпадение → reconcile.

### 9.3 Zero-crossing
При переходе через 0:
- старая Leg считается закрытой,
- создаётся новая LegState.

---

## 10. События Position Model

Публикуются в EventBus:

```
position.updated
position.reconciled
position.dd_violation
position.size_limit
position.on_zero_cross
```

---

## 11. Хранение позиции в Storage

В Storage сохраняется:

```
state.positions[symbol] = PositionSnapshot
```

Не хранится:
- история всех обновлений,
- стакан изменений.

Только "истина последнего состояния".

---

## 12. Роль Position Model в BotPlatform

Position Model обеспечивает:

- точный и согласованный расчёт PnL,
- одинаковую логику работы Legs и стратегий,
- правильный пересчёт средней цены,
- устойчивость к ошибкам бирж,
- возможность восстановления после сбоев.

Position Model — это «сердце учёта» всей BotPlatform.
