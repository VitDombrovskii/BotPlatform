
# 19-leg-architecture.md — Архитектура Legs в BotPlatform

## 1. Что такое Leg

**Leg** — это атомарный торговый модуль стратегии.  
Он отвечает за управление одной направленной позицией (LONG или SHORT), включая:

- вход,
- выход,
- scale-in / scale-out,
- bubble-алгоритм,
- риск-ограничения.

Leg — минимальный строительный блок стратегии.  
Стратегия собирает Legs, как конструктор.

---

## 2. Где Leg расположен в системе

```
StrategyEngine
   │
   ├── Strategy
   │      ├── LongLeg
   │      └── ShortLeg
   │
ExecutionEngine
```

Стратегия не содержит сложной логики — она делегирует Legs.

---

## 3. Жизненный цикл Leg

```
1. Инициализация
2. Получение StrategyContext
3. Принятие решений (ActionIntent)
4. Передача намерений в StrategyEngine
5. Получение событий ордеров и обновление состояния
6. Повтор цикла
```

---

## 4. Компоненты Leg

```
Leg
├── State
│   ├── size
│   ├── entry_price
│   ├── realized_pnl
│   ├── bubble_state
│   ├── scale_state
│   └── risk_state
│
├── Controllers
│   ├── BubbleController
│   ├── ScaleController
│   └── RiskController
│
└── Decision Engine
    ├── should_open()
    ├── should_close()
    ├── should_scale_in()
    ├── should_scale_out()
    └── build_intents()
```

---

## 5. Состояние Leg

```python
class LegState:
    side: str
    size: float
    entry_price: float
    realized_pnl: float
    unrealized_pnl: float
    bubble_state: dict
    scale_state: dict
    risk_state: dict
```

Состояние полностью сериализуемо → можно сохранять, восстанавливать, тестировать.

---

## 6. Decision Engine

```python
should_open(ctx)
should_close(ctx)
should_scale_in(ctx)
should_scale_out(ctx)
build_intents(ctx)
```

Leg принимает решения на основе StrategyContext — стратегический слой только собирает ответы Legs.

---

## 7. Bubble внутри Leg

BubbleController инкапсулирован:

- открывает локальную мини-позицию при движениях,
- закрывает её локально в плюс,
- корректирует entry и size Leg,
- обновляет bubble_state.

Стратегия не знает о bubble — всё внутри Leg.

---

## 8. Scale внутри Leg

ScaleController управляет:

- уровнями scale-in,
- уровнями scale-out,
- ограничениями по размеру,
- обновлением scale_state.

Scale — тоже часть Leg, а не стратегии.

---

## 9. Risk внутри Leg

RiskController:

- ограничивает DD Leg,
- блокирует переоткрытие,
- проверяет sanity-check,
- лимитирует ордеры.

Risk — фильтр на ActionIntent.

---

## 10. Изоляция Legs

LongLeg и ShortLeg полностью независимы:

- разные entry,
- разный размер,
- разные контроллеры,
- независимый bubble,
- независимый scale,
- независимый риск.

Позволяет:

- хедж-стратегию,
- multi-leg стратегии,
- cross-exchange legs.

---

## 11. Протокол Leg

```python
class Leg(Protocol):
    def on_tick(self, ctx) -> list[ActionIntent]: ...
    def on_order_update(self, update): ...
    def get_state(self) -> LegState: ...
    def load_state(self, state: LegState): ...
```

Стратегия взаимодействует только через этот слой.

---

## 12. Пример Leg в стратегии

```python
class HedgeStrategy:
    def __init__(self, cfg):
        self.long_leg = LongLeg(cfg.long)
        self.short_leg = ShortLeg(cfg.short)

    def on_tick(self, ctx):
        intents = []
        intents += self.long_leg.on_tick(ctx)
        intents += self.short_leg.on_tick(ctx)
        return intents
```

Стратегия → просто контейнер Legs.

---

## 13. Масштабируемость Leg Architecture

Позволяет создавать:

- HedgeLEGS,
- ArbitrageLEGS,
- SpreadLEGS,
- Multi-symbol LEGS,
- Multi-exchange LEGS.

Leg — универсальный атом стратегии.

---

## 14. Роль Leg Architecture

Leg Architecture делает стратегию:

- простой,
- модульной,
- расширяемой,
- устойчивой,
- переносимой.

Leg — «клетка» торгового организма.
