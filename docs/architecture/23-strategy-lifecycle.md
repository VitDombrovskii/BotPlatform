
# 23-strategy-lifecycle.md — Жизненный цикл стратегии в BotPlatform

## 1. Назначение документа

Стратегия — это высокоуровневый мозговой центр, который:
- создаёт Legs,
- управляет ими,
- принимает торговые решения,
- взаимодействует с RiskSystem,
- отправляет ActionIntent → ExecutionEngine.

Жизненный цикл стратегии определяет:
- как стратегия запускается,
- как она получает данные,
- как она работает на каждом тике,
- как отключается,
- как восстанавливается после падений.

---

## 2. Общая схема жизненного цикла

```
1. Загрузка конфигурации
2. Инициализация стратегии
3. Создание Legs
4. Загрузка сохранённого состояния (если есть)
5. Runtime:
     5.1 Получение MarketSnapshot
     5.2 Получение SignalSnapshot
     5.3 Формирование StrategyContext
     5.4 Вызов Legs → ActionIntents
     5.5 RiskSystem фильтрует Intents
     5.6 StrategyEngine передаёт их ExecutionEngine
     5.7 Получение OrderUpdates → обновление Legs
6. Периодическое сохранение состояния
7. Graceful Shutdown
8. Recovery после перезапуска
```

---

## 3. Фаза 1 — загрузка конфигурации

Стратегия получает свою конфигурацию из ConfigSystem:

```yaml
strategy:
  hedge:
    enabled: true
    long:
      base_size: 0.01
    short:
      base_size: 0.01
```

ConfigSystem гарантирует:
- типизацию,
- валидацию,
- наличие всех параметров,
- горячее обновление при необходимости.

---

## 4. Фаза 2 — инициализация стратегии

Платформа вызывает:

```python
strategy = HedgeStrategy(config)
```

Во время инициализации стратегия:
- разогревает внутренние структуры,
- анализирует конфиг,
- готовит ресурсы,
- подготавливает Legs.

Но ничего не торгует.

---

## 5. Фаза 3 — создание Legs

Стратегия создает свои Legs:

```python
self.long_leg = LongLeg(config.long)
self.short_leg = ShortLeg(config.short)
```

Каждая Leg:
- получает локальную часть конфигурации,
- создаёт свои контроллеры: bubble, scale, risk,
- создаёт пустой LegState.

---

## 6. Фаза 4 — загрузка сохранённого состояния

Если StorageLayer нашел предыдущее состояние:

```
state.strategy["hedge"] → передается в стратегию
state.legs["hedge.long"] → передается в LongLeg
state.legs["hedge.short"] → передается в ShortLeg
```

Таким образом:
- восстанавливается entry_price,
- восстанавливается size,
- восстанавливается bubble_state и scale_state,
- стратегия продолжает жить без перерыва.

---

## 7. Фаза 5 — runtime работа стратегии

Цикл для каждого тика:

```
StrategyEngine получает market.snapshot
↓
StrategyEngine получает signal.snapshot
↓
формирует StrategyContext
↓
strategy.on_tick(ctx)
↓
Leg.on_tick(ctx) возвращает ActionIntents
↓
RiskSystem фильтрует intents
↓
ExecutionEngine исполняет intents
↓
OrderUpdates вернутся в Leg
```

Стратегия не должна:
- работать с ордерами напрямую,
- обращаться к бирже,
- заниматься масштабированием.

Стратегия только координирует Legs.

---

## 8. StrategyContext — сердце цикла

Стратегия получает минимальный набор данных:

```python
class StrategyContext:
    symbol: str
    market: MarketSnapshot
    signals: SignalSnapshot
    position: PositionSnapshot | None
```

Контекст передаётся Legs.

---

## 9. Фаза 6 — сохранение состояния

Периодически StrategyEngine вызывает:

```python
state = strategy.get_state()
storage.save_strategy_state(name, state)
```

Сохраняются:
- размеры Legs,
- bubble_state,
- scale_state,
- risk_state,
- настройки стратегии.

---

## 10. Фаза 7 — Graceful Shutdown

При остановке:

1. Стратегия сообщает Leg-ам о shutdown.
2. Legs завершают внутренние процессы.
3. StrategyEngine сохраняет state.
4. Движки закрывают WebSocket/REST.
5. Публикуется событие:
```
system.strategy_shutdown
```

---

## 11. Фаза 8 — Recovery (восстановление)

После перезапуска:

1. Загружается последнее состояние.
2. Проводится сверка с биржей:
   - реальные активные ордера,
   - размер позиции.
3. При расхождениях стратегия:
   - корректирует LegState,
   - может загрузить emergency-mode.
4. Стратегия продолжает цикл on_tick.

---

## 12. События Strategy Lifecycle

Платформа генерирует:

```
strategy.loaded
strategy.initialized
strategy.state_restored
strategy.tick_processed
strategy.intent_emitted
strategy.error
strategy.shutdown
```

---

## 13. Ошибки стратегии

Если стратегия падает:
- StrategyEngine перезапускает её,
- state восстанавливается,
- bubble/scale уровни не теряются,
- потерянные intents не дублируются.

---

## 14. Жизненный цикл Legs внутри стратегии

Каждая Leg живет в том же цикле:

```
Leg initialized
Leg loads state
Leg receives ctx
Leg produces intents
Leg receives order updates
Leg updates local state
```

Стратегия — просто дирижёр, а Legs — музыканты.

---

## 15. Роль Strategy Lifecycle

Strategy Lifecycle обеспечивает:

- модульность,
- предсказуемость,
- отказоустойчивость,
- совместимость между стратегиями,
- лёгкость тестирования,
- возможность горячей замены стратегий.

Жизненный цикл стратегии — каркас, на котором держится BotPlatform.
