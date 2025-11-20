
# 07-market-data-engine.md — Market Data Engine в BotPlatform

## 1. Назначение Market Data Engine

Market Data Engine — это источник правды о состоянии рынка.  
Он отвечает за получение данных от бирж, их нормализацию и публикацию в EventBus.

Основная роль:
**Биржа → Market Data Engine → MarketSnapshot → EventBus → Остальные движки.**

Без надёжной и быстрой подачи данных остальные уровни не смогут работать корректно.

---

## 2. Какие данные получает движок

Market Data Engine может получать:

- цены (last price, mark price),
- стакан (order book),
- торговые события (trades),
- funding rate,
- индексные данные,
- открытый интерес,
- данные о ликвидациях,
- системные данные биржи.

Тип данных зависит от возможностей биржи и выбранного конфига.

---

## 3. Основные компоненты движка

```
MarketDataEngine
├── ExchangeAdapter (Binance/BingX/OKX…)
├── Normalizer
├── SnapshotBuilder
└── Publisher (EventBus)
```

### 3.1 ExchangeAdapter
Интерфейс общения с биржей:
- websockets
- http-poll
- гибридный режим

### 3.2 Normalizer
Приводит данные разных бирж к одному формату.

### 3.3 SnapshotBuilder
Строит итоговый `MarketSnapshot`, включающий:
- symbol,
- price,
- volume,
- orderbook,
- trades,
- timestamps.

### 3.4 Publisher
Публикует событие:
```
event.type = "market.snapshot"
event.payload = MarketSnapshot
```

---

## 4. MarketSnapshot — структура данных

Все движки получают именно эту структуру.

```python
class MarketSnapshot:
    symbol: str
    timestamp: float
    price: float
    mark_price: float
    bid: float
    ask: float
    bid_volume: float
    ask_volume: float
    funding_rate: float | None
    orderbook: List[OrderBookLevel]
    trades: List[Trade]
```

Минимальный набор: цена + время.

---

## 5. Реализации потока данных

Market Data Engine может работать в трёх режимах:

### 5.1 WebSocket Streaming (предпочтительный режим)
- минимальная задержка,
- постоянный поток данных,
- идеально для алготорговли.

### 5.2 HTTP Polling (fallback)
- запросы раз в N миллисекунд,
- полезно для бирж без ws-стакана.

### 5.3 Гибридный режим
- WS: цены и trades,
- HTTP: open interest, funding, медленные данные.

---

## 6. Поддержка нескольких бирж

Один движок может управлять несколькими адаптерами:

```
BinanceAdapter + BingXAdapter + OKXAdapter → Market Data Engine
```

Данные нормализуются и публикуются в общем формате.

---

## 7. EventBus взаимодействие

Market Data Engine:
- слушает события системы (`system.heartbeat`, `system.config_reload`)
- публикует только одно событие:
  ```
  market.snapshot
  ```

Период публикации зависит от стратегии:
- high frequency: до 1000 тик/сек
- обычные стратегии: 1–10 тик/сек

---

## 8. Масштабирование

### 8.1 Горизонтальное
- по биржам (один процесс на биржу),
- по symbols (один движок на символ),
- по L3 orderbook (отдельный процесс для агрегации).

### 8.2 Вертикальное
- увеличение частоты опроса,
- расширение структуры данных (добавить ликвидации, OI, потоки).

---

## 9. Надёжность Market Data Engine

Для устойчивой работы внедряются механизмы:
- автоматическое переподключение сокетов,
- heartbeat-monitor,
- проверка отставания данных,
- fallback на резервный источник,
- логирование задержек.

---

## 10. Пример жизненного цикла тика

```
1. Binance WS сообщает trade
2. ExchangeAdapter принимает данные
3. Normalizer приводит к единому виду
4. SnapshotBuilder формирует MarketSnapshot
5. Engine публикует событие market.snapshot
6. SignalsEngine получает событие
7. StrategyEngine получает новое событие
```

---

## 11. Роль в BotPlatform

Market Data Engine — фундамент всех торговых решений.

Без качественных рыночных данных:
- сигналы будут неверны,
- стратегии будут неадекватно реагировать,
- ордера будут отправляться с запозданием.

Market Data Engine обеспечивает:
- своевременность,
- точность,
- консистентность.

