# Пункт B — Структура директорий и модулей BotPlatform

Этот документ уточняет дерево директорий проекта BotPlatform и распределение ответственности между верхнеуровневыми модулями. Он конкретизирует общую схему из `01-platform-blueprint.md`.

---

## 1. Общая структура проекта

Базовая структура корня репозитория:

```text
BotPlatform/
├── core/
├── exchanges/
├── engines/
├── strategies/
├── signals/
├── storage/
├── monitoring/
├── notifications/
├── admin/
├── docs/
└── main.py
```

Назначение каждого модуля:

- `core/` — общие типы, модели, события, Intent'ы, утилиты.
- `exchanges/` — адаптеры бирж (Binance, BingX, OKX и т.д.).
- `engines/` — системные движки (market data, signals, strategies, execution).
- `strategies/` — конкретные стратегии (hedge_v2, breakout, grid, и т.д.).
- `signals/` — независимые модули сигналов и индикаторов.
- `storage/` — слой хранения (state, логи, БД).
- `monitoring/` — дашборды, метрики, web-интерфейсы.
- `notifications/` — Telegram, email и другие уведомления.
- `admin/` — административные модули (пользователи, права, лимиты).
- `docs/` — документация (архитектура, спецификации, заметки).
- `main.py` — точка входа в платформу.

---

## 2. Модуль core/

Дерево:

```text
core/
├── __init__.py
├── models.py
├── snapshots.py
├── intents.py
├── events.py
├── event_bus.py
├── utils.py
└── config_loader.py
```

Назначение:

- `models.py` — базовые доменные модели (Symbol, Timeframe, Side и т.п.).
- `snapshots.py` — структуры данных для:
  - `MarketSnapshot`,
  - `PositionSnapshot`,
  - `AccountSnapshot`,
  - `SignalSnapshot` (общий базовый тип).
- `intents.py` — намерения:
  - `ActionIntent` (от стратегии),
  - `OrderIntent` (к бирже),
  - вспомогательные структуры.
- `events.py` — типы событий для EventBus:
  - `MarketEvent`, `SignalEvent`, `StrategyEvent`, `OrderEvent`, `SystemEvent`.
- `event_bus.py` — реализация шины событий (локальная или обёртка для внешнего брокера).
- `utils.py` — общие утилиты (таймштампы, конвертации, безопасные вызовы).
- `config_loader.py` — загрузка и валидация конфигов (YAML/JSON → Pydantic/Typed).

`core/` не зависит от конкретных бирж, стратегий и движков — это фундамент.

---

## 3. Модуль exchanges/

Дерево (целевое):

```text
exchanges/
├── __init__.py
├── base.py
├── binance/
│   ├── __init__.py
│   ├── client.py
│   └── models.py
├── bingx/
│   ├── __init__.py
│   ├── client.py
│   └── models.py
└── okx/
    ├── __init__.py
    ├── client.py
    └── models.py
```

Назначение:

- `base.py` — абстрактный интерфейс `Exchange`:
  - `get_market_snapshot()`,
  - `get_positions()`,
  - `place_order(order_intent)`,
  - `stream_market_data(callback)`.
- Подпапки (`binance/`, `bingx/`, `okx/`) — реализация интерфейса под конкретные API.

Стратегии и движки работают с `Exchange` через общий интерфейс, не зная деталей реализаций.

---

## 4. Модуль engines/

Дерево:

```text
engines/
├── __init__.py
├── market_data_engine.py
├── signals_engine.py
├── strategy_engine.py
├── execution_engine.py
└── scheduler.py
```

Назначение:

- `market_data_engine.py` — опрашивает биржи, формирует `MarketSnapshot`, публикует `MarketEvent` в EventBus.
- `signals_engine.py` — вызывает модули из `signals/`, формирует `SignalSnapshot` и публикует `SignalEvent`.
- `strategy_engine.py` — передаёт данные стратегиям:
  - собирает `MarketSnapshot` + `SignalSnapshot` + `PositionSnapshot`,
  - вызывает стратегии,
  - получает `ActionIntent`,
  - публикует `StrategyEvent`.
- `execution_engine.py` — преобразует `ActionIntent` → `OrderIntent` и вызывает `Exchange.place_order`, публикует `OrderEvent`.
- `scheduler.py` — планировщик периодических задач (тик движков, бэкапы, housekeeping).

Движки не содержат логики стратегий — они только маршрутизируют данные и намерения.

---

## 5. Модуль strategies/

Дерево:

```text
strategies/
├── __init__.py
├── hedge_v2/
│   ├── __init__.py
│   ├── config_schema.py
│   ├── strategy.py
│   └── leg/
│       ├── __init__.py
│       ├── state.py
│       ├── leg.py
│       ├── pnl.py
│       ├── scale_in.py
│       ├── scale_out.py
│       └── bubbles.py
└── examples/
    ├── simple_long/
    └── breakout_demo/
```

Назначение:

- `hedge_v2/` — твоя основная многоногая стратегия с пузырьками (Variant C).
- `config_schema.py` — Pydantic/typed-схема конфигурации конкретной стратегии.
- `strategy.py` — основной класс стратегии:
  - инициализирует ноги,
  - определяет, какие сигналы использовать,
  - обрабатывает входящие snapshots,
  - возвращает список `ActionIntent`.
- `leg/` — реализация Leg Engine (см. `02-leg-engine.md`).

Папка `examples/` — простые стратегии для тестов и демонстраций.

---

## 6. Модуль signals/

Дерево:

```text
signals/
├── __init__.py
├── base.py
├── flow/
│   ├── __init__.py
│   └── flow_signal.py
├── indicators/
│   ├── __init__.py
│   ├── rsi.py
│   ├── ema.py
│   └── macd.py
└── volume/
    ├── __init__.py
    ├── cvd.py
    └── oi.py
```

Назначение:

- `base.py` — общий интерфейс сигналов:
  - `update(market_snapshot)`,
  - `snapshot() -> SignalSnapshot`.
- Подпапки реализуют:
  - потоковые сигналы (flow),
  - классические индикаторы,
  - объёмные и деривативные сигналы (CVD, OI).

Signals Engine вызывает эти модули и публикует их результаты как события.

---

## 7. Модуль storage/

Дерево:

```text
storage/
├── __init__.py
├── state/
│   ├── __init__.py
│   ├── state_repository.py
│   └── serializers.py
├── logs/
│   ├── __init__.py
│   ├── trade_logs/
│   └── system_logs/
└── db/
    ├── __init__.py
    ├── sqlite_backend.py
    └── migrations/
```

Назначение:

- `state/` — сохранение и восстановление состояния стратегий, ног, движков.
- `logs/` — логи исполнения (можно интегрировать с logging, но иметь структуру).
- `db/` — адаптеры БД, миграции.

На раннем этапе можно использовать файловое хранилище (JSON/SQLite), но структура уже закладывается.

---

## 8. Модуль monitoring/

Дерево:

```text
monitoring/
├── __init__.py
├── dashboard/
│   ├── __init__.py
│   ├── server.py
│   └── views/
└── metrics/
    ├── __init__.py
    ├── collectors.py
    └── exporters.py
```

Назначение:

- `dashboard/` — web-интерфейс для:
  - просмотра состояния стратегий,
  - позиций,
  - сделок,
  - логов пузырьков и ног.
- `metrics/` — сбор и экспорт метрик (Prometheus-style или свои).

---

## 9. Модуль notifications/

Дерево:

```text
notifications/
├── __init__.py
├── telegram_bot.py
└── alerts.py
```

Назначение:

- `telegram_bot.py` — приём и отправка сообщений в Telegram.
- `alerts.py` — правила:
  - когда слать уведомления,
  - по каким событиям,
  - в каком формате.

Источник данных — EventBus и Storage.

---

## 10. Модуль admin/

Дерево (на будущее):

```text
admin/
├── __init__.py
├── users.py
├── permissions.py
└── risk_profiles.py
```

Назначение:

- пользователи,
- их стратегии,
- их ключи бирж,
- права и лимиты.

Это задел под много-пользовательскую платформу.

---

## 11. Модуль docs/

Структура:

```text
docs/
├── architecture/
│   ├── 01-platform-blueprint.md
│   ├── 02-leg-engine.md
│   └── 03-directory-structure.md
└── notes/
    └── ...
```

Документация живёт рядом с кодом и развивается вместе с платформой.

---

## 12. main.py

`main.py` — точка входа:

- инициализирует конфиг,
- поднимает EventBus,
- инициализирует движки,
- выбирает стратегию,
- запускает основной цикл (или оркестрацию).

Детали запуска будут уточняться в следующих документах.
