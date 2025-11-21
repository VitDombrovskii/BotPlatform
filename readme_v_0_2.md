# BotPlatform v0.2 — Documentation

Добро пожаловать в **BotPlatform v0.2** — первую полностью рабочую, модульную версию бота. Эта версия строит фундамент архитектуры, который в дальнейшем позволит масштабировать систему вплоть до многобиржевых и мультистратегийных сценариев.

## Что входит в версию v0.2

BotPlatform v0.2 — это минимальный, но полностью функционирующий конвейер:

- **EventBus** — асинхронная шина событий.
- **FakeMarketEngine** — генератор рыночных данных.
- **MockExchange** — симулятор биржи, исполняющий ордера.
- **ExecutionEngine (Local)** — отправка ордеров и публикация результатов.
- **LongLeg / ShortLeg** — минимальные ноги.
- **HedgeStrategy** — первая стратегия.
- **StrategyRuntime** — связующее звено между движками.
- **main.py** — runnable demo.

Всё собрано строго по архитектурным документам.

---

# 1. Архитектура целиком

Основная идея BotPlatform — разделить бота на независимые модули, каждый выполняет свою роль:

```
                +-------------------+
                |   FakeMarketEngine|
                +---------+---------+
                          |
                    market.snapshot
                          |
                     +----v-----+
                     | EventBus |
                     +--+----+--+
                        |    |
        market.snapshot |    | order.update
                        |    |
            +-----------v    v-------------+
            |       StrategyRuntime        |
            | (StrategyEngine + Runtime)  |
            +-------+----------------------+
                    |
                    | OrderIntent
                    v
          +------------------------+
          | LocalExecutionEngine   |
          +-----------+------------+
                      |
                      | place_order()
                      v
                +------------+
                | MockExchange|
                +------------+
```

Конвейер замкнут: MockExchange создаёт `OrderUpdate`, отправляет назад в EventBus, и стратегия получает их.

---

# 2. Модули

## 2.1 EventBus
Асинхронная очередь публикации/подписки на события.
Реализует фундаментальный обмен сообщениями между движками.

Типы событий v0.2:
- `market.snapshot`
- `order.update`

---

## 2.2 FakeMarketEngine
Генерирует цену и создаёт рыночные снимки (`MarketSnapshot`).
Используется для тестов и разработки.

---

## 2.3 MockExchange
Полная симуляция биржи:
- сразу заполняет ордера как FILLED,
- обновляет позиции,
- считает realized PnL,
- формирует `OrderUpdate`.

---

## 2.4 ExecutionEngine (Local)
Принимает OrderIntent, отдаёт их в биржу и пробрасывает OrderUpdate в EventBus.

---

## 2.5 Legs

### LongLeg / ShortLeg
Пока минимальные:
- если позиции нет → открыть базовый размер.
- bubble/scale/risk уже подключены как пустые контроллеры.

---

## 2.6 HedgeStrategy
Стратегия, объединяющая две ноги: LONG и SHORT.
Пока только открывает обе позиции.

---

## 2.7 StrategyRuntime
Самый важный компонент v0.2:
- подписывается на market.snapshot,
- формирует StrategyContext,
- вызывает StrategyEngine,
- преобразует ActionIntent → OrderIntent,
- отправляет ордера,
- слушает order.update.

---

## 2.8 main.py
Запускает весь конвейер на 5 секунд.

Запуск:
```
python main.py
```

---

# 3. Ограничения v0.2 (и что будет в v0.3)

### Уже работает:
- генерация данных;
- принятие решений в стратегии;
- placing ордеров;
- формирование позиций;
- события order.update;
- полный loop решений.

### В следующей версии планируется:
- Legs обновляют состояние по OrderUpdate;
- StrategyRuntime ведёт карту позиций;
- bubble/scale начинают работать;
- добавится risk-системы;
- multi-symbol и multi-strategy;
- логирование в файлы;
- websockets BingX.

---

# 4. README (готовый для GitHub)

## BotPlatform v0.2 — Modular Trading Architecture

### Overview
BotPlatform is a modular, event-driven algorithmic trading system written in Python. Version **v0.2** implements a full working pipeline with simulated market data, exchange execution, strategy runtime, legs, and event bus.

### Features
- Modular architecture
- EventBus-based communication
- FakeMarketEngine for testing
- MockExchange with position simulation
- LocalExecutionEngine
- Long & Short Legs
- Hedge Strategy
- Strategy Runtime
- Fully runnable main.py

### Run Demo
```
pip install -r requirements.txt
python main.py
```

### Project Structure
```
botplatform/
  core/
  engines/
  exchanges/
  strategies/
  legs/
  controllers/
  storage/
  utils/
main.py
```

### Next Steps
- Real exchange connectors (BingX, Binance)
- Persistent storage
- Web dashboards
- Rich strategies and legs
- Risk, bubble, scale controllers

---
# Конец документа

