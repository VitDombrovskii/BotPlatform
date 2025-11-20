
# 22-risk-system.md — Risk System в BotPlatform

## 1. Назначение Risk System

Risk System — это защитный слой BotPlatform, который предотвращает:

- чрезмерный риск,
- переразгон позиций,
- неконтролируемый scale или bubble,
- входы в неблагоприятных условиях,
- критические просадки Legs или стратегии в целом.

Risk System работает на двух уровнях:

1. **Local Risk (внутри Leg)**
2. **Global Risk (вся стратегия или весь аккаунт)**

---

## 2. Архитектура Risk System

```
RiskSystem
├── LegRiskController
└── GlobalRiskController
```

---

## 3. LegRiskController — локальные риски Legs

Каждая Leg содержит собственный RiskController:

```
Leg
│
└── RiskController
```

Он защищает Leg от:

- чрезмерного размера позиции,
- чрезмерного DD,
- опасных входов/scale/bubble,
- частых повторных входов,
- выхода за пределы risk_state.

### Пример структуры локальных рисков:

```python
risk_state = {
    "max_size": 0.3,
    "max_dd_pct": 8.0,
    "cooldown_secs": 15,
    "last_entry_ts": None,
    "max_scale_levels": 5,
}
```

---

## 4. Локальные ограничения RiskController

### 4.1 Max Position Size
Не позволяет Leg увеличивать объём выше заданного лимита:

```
if new_size > max_size:
    reject scale-in
```

### 4.2 Max Drawdown per Leg
Если просадка Leg превышает max_dd_pct — Leg:

- блокирует scale-in,
- блокирует bubble,
- разрешает только scale-out или close.

### 4.3 Cooldown (откат времени)
Пауза между входами:

```
now - last_entry_ts < cooldown_secs → reject
```

### 4.4 Защита от флуда ордерами
Если Leg пытается отправить слишком много ордеров:

```
order_count > threshold → reject
```

### 4.5 Ограничение bubble
BubbleController не может работать, если:

- цена слишком волатильна,
- Leg близко к стоп-зоне,
- размер Leg слишком мал.

---

## 5. GlobalRiskController — глобальное управление рисками стратегии

GlobalRiskController управляет:

- общим размером позиции по символу,
- корреляцией Legs,
- максимальным DD стратегии,
- полосами риска (risk bands),
- авто-выключением Legs и стратегий.

---

## 6. Пример global risk state

```python
global_risk_state = {
    "strategy_max_dd_pct": 15,
    "strategy_max_size": 0.6,
    "symbol_exposure_limit": 0.8,
    "allow_hedge_conflicts": False,
    "auto_disable_strategy_on_limit": True
}
```

---

## 7. Механизмы глобального риска

### 7.1 Ограничение суммарного размера Legs

Для Hedge:

```
long_leg.size + short_leg.size <= strategy_max_size
```

### 7.2 Symbol Exposure Limit
Если стратегия использует 2+ Legs на один символ:

```
sum(abs(size)) <= symbol_exposure_limit
```

### 7.3 Просадка стратегии

```
total_unrealized_pnl_pct < -strategy_max_dd_pct
    → disable scale
    → force strategy to reduce risk
```

### 7.4 Hedge Conflict Control

Если long и short одновременно пытаются увеличить объём:

```
allow_hedge_conflicts = False → reject one of them
```

### 7.5 Auto-disable Strategy

При превышении лимита:

```
if auto_disable_strategy_on_limit:
    disable strategy
```

---

## 8. Decision Pipeline с Risk System

Правильный порядок принятия решений внутри Leg:

```
BubbleController → ScaleController → RiskController → build_intents
```

Правильный порядок на уровне стратегии:

```
Leg decisions → GlobalRiskController → ExecutionEngine
```

---

## 9. Как Risk System взаимодействует с EventBus

Публикуемые события:

```
risk.limit_reached
risk.dd_warning
risk.position_blocked
risk.strategy_disabled
risk.leg_dd_violation
```

Storage сохраняет risk events для анализа.

---

## 10. Роль Risk System

Risk System — «иммунная система» платформы:

- останавливает неконтролируемые движения,
- делает Legs более предсказуемыми,
- защищает стратегию от редких катастрофических сценариев,
- повышает живучесть торгового алгоритма,
- обеспечивает стабильный рост на долгой дистанции.

Без Risk System любая сложная стратегия превращается в хаос.

