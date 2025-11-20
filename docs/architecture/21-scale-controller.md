
# 21-scale-controller.md — Scale Controller в Leg Architecture

## 1. Назначение Scale Controller

**Scale Controller** — это часть Leg, отвечающая за:
- увеличение позиции (scale-in),
- уменьшение позиции (scale-out),
- управление уровнями и прогрессией,
- сглаживание входов и выходов,
- регуляцию риска.

Scale — это основной механизм адаптации Leg к рынку.  
Если Bubble — локальный микрокорректор,  
то Scale — стратегический регулятор размера позиции.

---

## 2. Место Scale Controller в архитектуре Leg

```
Leg
│
├── BubbleController
├── ScaleController   ← этот документ
└── RiskController
```

Scale работает **только внутри Leg**,  
и не пересекается с двухсторонней логикой Short/Long.

---

## 3. Цели Scale Controller

1. **Гладкое увеличение позиции**  
   Добавляется объём, когда цена идёт в нужном направлении.

2. **Гладкое сокращение позиции**  
   Если рынок уходит против Leg, Scale задолжен уменьшить объём.

3. **Предотвращение перегрузки позиции**  
   Scale контролирует max_size.

4. **Логика уровнями** (multi-level scale)  
   Позволяет строить сетку контрольных уровней.

---

## 4. Scale State

Scale сохраняется в LegState:

```python
scale_state = {
    "levels_triggered": 0,
    "max_levels": 5,
    "scale_in_pct": 0.6,
    "scale_out_pct": 0.8,
    "level_factor": 1.4,
    "last_scale_price": None
}
```

### Поля:

- **levels_triggered** — сколько уровней уже сработало.
- **max_levels** — максимальное количество уровней (обычно 3–7).
- **scale_in_pct** — шаг движения цены в нашу сторону для увеличения позиции.
- **scale_out_pct** — шаг против нас для уменьшения.
- **level_factor** — множитель увеличения размера.
- **last_scale_price** — цена последнего scale.

---

## 5. Логика входа Scale-In

Scale-In — увеличение позиции, когда рынок подтверждает движение.

Пример:

```python
move = calc_pct_move(state.entry_price, ctx.market.price)

if move >= scale_in_pct * (levels_triggered + 1):
    trigger scale-in
```

Scale-In увеличивает:
- size,
- levels_triggered,
- last_scale_price.

Scale-In работает **в сторону позиции**:
- LONG → рост цены
- SHORT → снижение цены

---

## 6. Логика Scale-Out

Scale-Out — уменьшение позиции, когда рынок идёт против нас.

Пример:

```python
adverse_move = calc_pct_move(ctx.market.price, state.entry_price)

if adverse_move >= scale_out_pct:
    trigger scale-out
```

Scale-Out:
- уменьшает size,
- может сбрасывать levels_triggered,
- корректирует last_scale_price.

Scale-Out работает **против позиции**:
- LONG → падение цены
- SHORT → рост цены

---

## 7. Размеры уровней Scale-In

Обычно применяется геометрическая прогрессия:

```
base_size → base_size * level_factor → base_size * level_factor^2 → ...
```

Пример:

```
base_size = 0.01
level_factor = 1.6

Уровни:
0:  0.01
1:  0.016
2:  0.0256
3:  0.04096
```

---

## 8. Размеры Scale-Out

Scale-Out может:

1. Уменьшать объём фиксированно:
   ```
   reduce 20% per event
   ```

2. Уменьшать до предыдущего уровня scale:
   ```
   size → previous level size
   ```

3. Сбрасывать часть позиции до base_size.

---

## 9. Правила безопасности и ограничения

Scale Controller обязан:

- запрещать scale-in выше max_size,
- запрещать scale-out ниже base_size,
- сбрасывать уровни после принудительного закрытия Leg,
- не пересекаться с bubble,
- не масштабировать вблизи стоп-зон,
- игнорировать scale при высокой волатильности.

---

## 10. Алгоритм Scale Controller

```
1. Рассчитать движение цены относительно entry_price
2. Если движение в нашу сторону:
      проверить scale-in условия
3. Если движение против позиции:
      проверить scale-out условия
4. Проверить risk_controller перед подтверждением scale
5. Обновить scale_state
6. Вернуть ActionIntents
```

---

## 11. Inteгpация Scale Controller в Leg

Leg вызывает scale:

```python
intents += scale_controller.on_tick(ctx, state)
```

Scale никогда не создаёт Intent напрямую, минуя RiskController.

---

## 12. Порядок выполнения Bubble и Scale

Правильный порядок:

```
1. BubbleController
2. ScaleController
3. RiskController
4. Build ActionIntent
```

Bubble — локальная коррекция.  
Scale — стратегический регулятор размера.

---

## 13. Как Scale влияет на LegState

После успешного scale-in/out:

- `size` изменяется
- `entry_price` пересчитывается
- `levels_triggered` обновляется
- `last_scale_price` сохраняется

Пример пересчёта entry_price:

```
new_entry = (old_entry * old_size + price * scale_added) / new_size
```

---

## 14. Отвязка Scale от стратегии

Стратегия **не знает** про scale — всё внутри Leg.

Scale внутри Leg даёт:

- переносимость,
- модульность,
- стабильность,
- отсутствие пересечений с хедж-логикой.

---

## 15. Роль Scale Controller

Scale Controller превращает Leg в адаптивный организм:

- увеличивается во время тренда,
- сокращается при угрозе DD,
- держит уровни структурированными,
- защищает от переобъёма.

Scale — стратегический мотор Leg.
