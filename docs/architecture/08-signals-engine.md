
# 08-signals-engine.md — Signals Engine в BotPlatform

## 1. Назначение Signals Engine

Signals Engine — вычислительный слой платформы, который:
- принимает `MarketSnapshot` от EventBus,
- вызывает модули сигналов,
- формирует `SignalSnapshot`,
- публикует событие `signal.snapshot` для Strategy Engine.

Signals Engine — мост между сырыми рыночными данными и логикой стратегий.

---

## 2. Основные задачи

1. Слушать `market.snapshot`.
2. Передавать MarketSnapshot каждому сигнал-модулю.
3. Обновлять внутренний state сигналов.
4. Формировать объединённый `SignalSnapshot`.
5. Публиковать событие `signal.snapshot`.

---

## 3. Компоненты Signals Engine

```
SignalsEngine
├── SignalRegistry
├── SignalModules[]
├── SnapshotAggregator
└── Publisher (EventBus)
```

### 3.1 SignalRegistry
Управляет:
- загрузкой модулей,
- активацией/деактивацией сигналов,
- конфигами сигналов.

### 3.2 SignalModules[]
Каждый модуль сигналов:
- получает MarketSnapshot,
- обновляет свой внутренний state,
- отдаёт частичный сигнал.

Примеры модулей:
- RSI, EMA, MACD,
- CVD, OI, Delta,
- Flow signal,
- волатильность,
- аномалии ликвидаций.

### 3.3 SnapshotAggregator
Собирает значения сигналов в единый словарь:
```
{"rsi": 54.2, "ema_fast": 72200.4, "cvd": -1540, ...}
```

### 3.4 Publisher
Публикует событие `signal.snapshot`.

---

## 4. Структура SignalSnapshot

```python
class SignalSnapshot:
    symbol: str
    timestamp: float
    values: Dict[str, Any]
```

Пример:
```json
{
  "symbol": "BTCUSDT",
  "timestamp": 1710000012.0,
  "values": {
      "rsi": 61.4,
      "ema_fast": 72010,
      "ema_slow": 70500,
      "cvd": -2145,
      "flow": {"side": "long", "confidence": 0.78}
  }
}
```

---

## 5. Взаимодействие с EventBus

**Слушает:**
```
market.snapshot
```

**Публикует:**
```
signal.snapshot
```

Цепочка взаимодействия:

```
MarketDataEngine → market.snapshot
SignalsEngine → signal.snapshot
StrategyEngine → strategy.decision
ExecutionEngine → order.*
```

---

## 6. Жизненный цикл обработки тика

```
1. Получен market.snapshot
2. Для каждого сигнала вызывается module.update(snapshot)
3. Каждый модуль формирует свой частичный сигнал
4. SnapshotAggregator объединяет данные
5. SignalsEngine публикует signal.snapshot
```

Signals Engine не хранит долгосрочную историю — это делают отдельные модули.

---

## 7. Интерфейс SignalModule

Все модули реализуют единый интерфейс:

```python
class SignalModule:
    def update(self, snapshot: MarketSnapshot): ...
    def snapshot(self) -> Dict[str, Any]: ...
    @property
    def name(self) -> str: ...
```

Это обеспечивает:
- модульность,
- независимость логики,
- расширяемость.

---

## 8. Масштабирование

### Горизонтальное:
- 1 движок на символ,
- 1 движок на группу сигналов,
- 1 движок на разные биржи.

### Вертикальное:
- добавление новых сигналов,
- многопоточная обработка тяжёлых вычислений,
- буферы исторических данных (для OI, CVD, свечей).

SignalsEngine легко делится на под-модули по частям логики.

---

## 9. Отказоустойчивость

При ошибке модуля:
- SignalsEngine продолжает работу,
- ошибка публикуется как `system.error`,
- модуль может быть автоматически отключён.

Механизмы безопасности:
- тайм-ауты на модули,
- защита от заблокировавшихся сигналов,
- мониторинг задержек.

---

## 10. Роль Signals Engine в архитектуре

Signals Engine — аналитический мозг, который:
- трансформирует сырые рыночные данные в полезные признаки,
- позволяет стратегиям быть простыми,
- создаёт унифицированное пространство сигналов,
- легко расширяется под любые будущие алгоритмы.

Без Signals Engine стратегиям пришлось бы:
- самостоятельно считать индикаторы,
- хранить историю,
- отслеживать множества потоков,
- смешивать расчётную логику с торговой.

Signals Engine делает архитектуру чистой и правильной.

