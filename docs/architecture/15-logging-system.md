
# 15-logging-system.md — Система логирования (Logging System) в BotPlatform

## 1. Назначение Logging System

Logging System — нервная система платформы.  
Она отвечает за:

- техническое логирование работы движков,
- структурированные записи событий,
- трассировку цепочек действий,
- детектирование ошибок,
- аналитическую диагностику,
- аудиторские журналы.

Логи должны быть:
- понятными,
- структурированными,
- пригодными для машинной обработки,
- удобными для человека,
- безопасными.

---

## 2. Архитектура Logging System

```
LoggingSystem
├── LogEmitter
├── StructuredLogger
├── TraceContext
├── LogRouter
└── LogSink(s)
     ├── Console
     ├── File
     ├── RotatingFile
     ├── EventStore
     └── External (ELK / Loki / CloudWatch / S3)
```

---

## 3. Типы логов

BotPlatform использует четыре типа логов:

```
runtime logs        — работа движков, запуск, остановка
event logs          — любые события EventBus
trade logs          — исполнение действий, ордера
system logs         — ошибки, предупреждения, статус
```

---

## 4. Структура лог-записи

Все логи структурированы:

```json
{
  "timestamp": 1710002810.123,
  "level": "INFO",
  "module": "strategy.engine",
  "message": "Strategy decision applied",
  "context": {
    "symbol": "BTCUSDT",
    "strategy": "hedge_leg",
    "correlation_id": "abc-123"
  }
}
```

---

## 5. Уровни логирования

Поддерживаются стандартные уровни:

- DEBUG — подробная техническая информация
- INFO — ключевые действия, нормальное поведение
- WARNING — отклонения от нормы, не фатально
- ERROR — ошибки, требующие внимания
- CRITICAL — критические сбои

---

## 6. Связь логов и EventBus

Каждый лог может иметь `correlation_id` — тот же, что у цепочки событий.

Пример цепочки:

```
strategy.decision (CID=abc)
→ order.submitted (CID=abc)
→ order.filled (CID=abc)
→ state.updated (CID=abc)
→ log("Position updated", CID=abc)
```

Это позволяет:

- собирать цепочки,
- просматривать полный жизненный цикл действий,
- писать инструменты анализа исполнения.

---

## 7. Логирование событий EventBus

Каждое событие может быть продублировано в лог:

```
event.market.log
event.strategy.log
event.order.log
```

Формат:

```json
{
  "event_type": "order.filled",
  "payload": {...},
  "timestamp": 1710003001.44
}
```

---

## 8. Структура логирования движков

### 8.1 MarketDataEngine
Логирует:
- ошибки сокетов
- reconnect
- обновление цены
- задержку тиков

### 8.2 Signals Engine
Логирует:
- ошибки модулей сигналов
- время расчётов
- задержку сигналов

### 8.3 Strategy Engine
Логирует:
- количество ActionIntent
- контекст стратегии (кратко)
- отключение/включение стратегий
- ошибочные решения

### 8.4 Execution Engine
Логирует:
- отправку ордера
- сбор сведений о статусах
- ошибки биржи
- превышение rate limit

---

## 9. Трассировка (TraceContext)

TraceContext — механизм связывания логов и событий.

```python
with TraceContext(correlation_id="xyz"):
    logger.info("Opening position")
```

TraceContext передаёт correlation_id вложенным вызовам.

---

## 10. LogRouter — маршрутизация логов

Позволяет отправить разные типы логов в разные места:

```
runtime → console + file
orders → file + S3
errors → Telegram + file
events → EventStore
```

---

## 11. LogSink — конечные хранилища логов

### 11.1 ConsoleSink
Вывод в stdout.

### 11.2 FileSink
Обычные файловые логи.

### 11.3 RotatingFileSink
Ротация по размеру/времени.

### 11.4 EventStoreSink
Хранение событий в базе данных.

### 11.5 ExternalSink
Поддержка:
- ELK
- Loki + Promtail
- CloudWatch
- Datadog
- S3/HDFS

---

## 12. Лог-файлы: структура каталогов

```
logs/
├── engine/
│   ├── market.log
│   ├── signals.log
│   ├── strategy.log
│   └── execution.log
├── events/
│   └── events.log
├── trades/
│   └── trades.log
└── system/
    └── errors.log
```

---

## 13. Live Debug Mode

Платформа поддерживает режим "живой отладки":

- прямой вывод всех событий,
- логирование каждого ActionIntent,
- логирование всех входов/выходов стратегии,
- ограничение по частоте (throttling).

---

## 14. Минимальный набор логов, обязательный для продакшена

- market engine errors
- execution errors
- order lifecycle
- strategy decisions
- system errors
- restart & recovery logs

---

## 15. Роль Logging System в BotPlatform

Logging System обеспечивает:

- прозрачность работы платформы,
- быструю диагностику,
- контроль работы стратегий,
- анализ исполнения,
- устойчивость,
- возможность построения внешнего мониторинга.

Логи — это то, что превращает BotPlatform из «бота» в серьёзную торговую систему.
