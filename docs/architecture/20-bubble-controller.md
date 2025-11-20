
# 20-bubble-controller.md — Bubble Controller в Leg Architecture

## 1. Назначение Bubble Controller

**Bubble Controller** — это локальный механизм внутри Leg, который:

- открывает мини‑позиции («пузырьки») при быстрых колебаниях цены,
- закрывает их с небольшой локальной прибылью,
- корректирует состояние Leg без влияния на стратегию целиком,
- сглаживает просадки (DD),
- работает независимо от основного входа/выхода Leg.

Bubble — это микроробот внутри Leg.

Bubble *не стратегия, не Leg и не внешний контроллер.*  
Bubble — строго внутренняя логика Leg.

---

## 2. Зачем нужен Bubble Controller

Bubble выполняет 3 важные функции:

1. **Локальная компенсация просадок**  
   При движении против позиции Leg, bubble может открыться и закрыться в плюс → уменьшив DD Leg.

2. **Улучшение средней цены Leg**  
   После успешного bubble entry → Leg пересчитывает:
   - entry_price,
   - realized_pnl,
   - size.

3. **Локальный PnL-мотор**  
   Bubble создаёт дополнительные микро‑выигрыши без изменения глобальной позиции.

---

## 3. Где Bubble находится в архитектуре

```
Leg
│
├── BubbleController
├── ScaleController
└── RiskController
```

Bubble живёт и умирает *только* в пределах Leg.

---

## 4. Жизненный цикл Bubble

```
1. Цена движется против Leg
2. BubbleController проверяет условия входа
3. Leg открывает bubble order
4. BubbleController ждёт локальную прибыль
5. BubbleController инициирует закрытие bubble
6. Leg обновляет bubble_state и общую позицию
7. Bubble завершается
```

Bubble не должен:
- открываться повторно, пока предыдущий bubble не завершён,
- вмешиваться в решение scale или основной логики Leg.

---

## 5. Bubble State

Bubble хранится в LegState:

```python
bubble_state = {
    "active": False,
    "entry_price": None,
    "size": 0.0,
    "levels_triggered": 0,
    "last_trigger_price": None,
    "target_profit_pct": 0.15,
    "max_levels": 3
}
```

Bubble может быть многоуровневым, но чаще → один уровень.

---

## 6. Логика входа Bubble

BubbleController решает вход:

```python
def should_trigger_bubble(self, ctx: StrategyContext, state: LegState) -> bool:
    if state.bubble_state["active"]:
        return False

    # Цена ушла против позиции на bubble_entry_pct
    adverse_move = calc_pct_move(state.entry_price, ctx.market.price)

    return adverse_move >= self.cfg.entry_pct
```

Примеры условий входа:

- цена ушла против позиции на X %,
- RSI < 30 (для LONG bubble),
- быстрый импульс объёма,
- trigger only once per position.

---

## 7. Логика выхода Bubble

Bubble закрывается при:

```python
target_profit_pct = state.bubble_state["target_profit_pct"]
bubble_pnl = calc_pct_move(state.bubble_state["entry_price"], ctx.market.price)

if bubble_pnl >= target_profit_pct:
    return True
```

Также bubble может форсированно закрываться:

- по времени,
- по прыжку цены,
- по риску.

---

## 8. Как Bubble влияет на LegState

После закрытия bubble Leg получает:

```
1. realized_pnl += pnl(bubble)
2. size корректируется
3. entry_price пересчитывается
4. bubble_state сбрасывается
```

Никаких внешних действий стратегия не делает — Leg обновляет всё сам.

---

## 9. Полный алгоритм Bubble

```
if bubble не активен:
    если цена ушла против Leg:
        открыть bubble
else:
    если bubble в прибыли:
        закрыть bubble
        обновить LegState
```

И всё. Bubble — маленький робот.

---

## 10. Инкапсуляция Bubble внутри Leg

Стратегия не знает о bubble.

ExecutionEngine не знает о bubble.

**Bubble — часть LegState и LegDecision.**

Это даёт:

- независимость,
- простоту,
- повторяемость,
- переносимость между Legs и стратегиями.

---

## 11. Multi-level bubble (опционально)

Можно включить:

```
max_levels: 3
level_factor: 1.5
```

Bubble будет открываться несколькими уровнями при дальнейшем движении против Leg.

Но уровни всегда:

- принадлежат только Leg,
- не пересекаются с scale,
- не работают для разных Legs одновременно.

---

## 12. Ошибки и защита

BubbleController имеет встроенные предохранители:

- не позволяет открывать bubble слишком часто,
- ограничивает max_levels,
- запрещает bubble при слишком маленьком размере Leg,
- не открывается рядом со стоп-зоной,
- не работает при экстремальных рыночных условиях.

---

## 13. Роль Bubble Controller

Bubble Controller — микрокорректор, который:

- уменьшает просадку,
- улучшает среднюю цену,
- создаёт локальную прибыль,
- делает Leg более живучей и гладкой.

Bubble — это локальное «оперативное вмешательство» внутри Leg.
