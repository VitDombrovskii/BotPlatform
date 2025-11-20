
# 17-plugin-system.md — Плагинная система (Plugin System) в BotPlatform

## 1. Назначение Plugin System

Plugin System — это механизм расширения BotPlatform без изменения исходного кода.  
Благодаря плагинам можно добавлять:

- новые стратегии,
- новые модули сигналов,
- новые биржевые адаптеры,
- новые движки,
- новые источники данных,
- новые форматтеры логов,
- интеграции с внешними API.

Плагинная система делает платформу:

- расширяемой,
- модульной,
- безопасной,
- устойчивой к обновлениям,
- пригодной для огромной экосистемы.

---

## 2. Архитектурная схема Plugin System

```
PluginSystem
├── PluginLoader
├── PluginRegistry
├── PluginSandbox
├── PluginValidator
└── PluginInterface(s)
     ├── StrategyPlugin
     ├── SignalPlugin
     ├── AdapterPlugin
     ├── EnginePlugin
     └── UtilityPlugin
```

---

## 3. Категории плагинов

### 3.1 Strategy Plugins
Реализуют стратегию:

```
class MyStrategy(StrategyPlugin):
    def on_tick(self, ctx):
        ...
```

### 3.2 Signal Plugins
Добавляют новые модули сигналов:

```
class VolumeSignal(SignalPlugin):
    def compute(self, market):
        return {"volume_spike": ...}
```

### 3.3 Adapter Plugins
Добавляют новые биржевые подключения:

```
class BitgetAdapter(AdapterPlugin):
    def send_order(...):
        ...
```

### 3.4 Engine Plugins
Позволяют заменять движки:

- нестандартные Execution Engines,
- кастомные Market Engines,
- внешние данные.

### 3.5 Utility Plugins
Любые интеграции:
- логирование,
- мониторинг,
- аналитика,
- алерты,
- внешние трейдинг-сигналы.

---

## 4. Структура плагина

Каждый плагин содержит:

```
plugin.yaml      — метаданные
__init__.py      — загрузка
plugin.py        — реализация
requirements.txt — зависимости (опционально)
```

Пример plugin.yaml:

```yaml
name: HedgeV2
type: strategy
version: 1.0.3
entrypoint: plugin.HedgeV2
description: Новый вариант хедж-стратегии
```

---

## 5. PluginLoader

Задачи:

- загрузить плагины по путям:
  - ./plugins/
  - ~/.botplatform/plugins/
  - системные каталоги
- проверить метаданные,
- инстанцировать классы,
- зарегистрировать их в реестре.

Плагины могут быть добавлены без рестарта (hot-loading).

---

## 6. PluginRegistry

Глобальный реестр:

```
registry.strategies
registry.signals
registry.adapters
registry.engines
registry.utilities
```

Registry позволяет:

- найти стратегию по имени,
- подключить нужный адаптер биржи,
- активировать сигнальный модуль,
- расширять pipeline.

---

## 7. PluginSandbox

Sandbox обеспечивает безопасность плагинов:

- ограничения CPU,
- ограничения памяти,
- ограничения доступа к сети,
- ограничение времени выполнения,
- запрет небезопасных операций.

Создание окружения:

```
sandbox = PluginSandbox(plugin)
sandbox.run_safely(...)
```

---

## 8. PluginValidator

Перед загрузкой проверяет:

- корректность plugin.yaml,
- соответствие PluginInterface,
- совместимость версии API,
- отсутствие вредоносного кода,
- корректность зависимостей.

При ошибке:

```
system.error (source="plugin.loader")
```

---

## 9. Жизненный цикл плагина

```
1. Загрузка метаданных
2. Проверка версии API
3. Инициализация класса (entrypoint)
4. Регистрация в реестре
5. Sandbox-обёртка
6. Интеграция в движки
7. Работа в runtime
8. Graceful unload (при отключении)
```

---

## 10. Пример подключения стратегии через плагин

```yaml
strategies:
  - name: HedgeV2
    plugin: HedgeV2
    config:
      base_size: 0.01
      bubble:
        enabled: true
        step_pct: 0.4
```

StrategyEngine выполнит:

```
plugin = registry.strategies["HedgeV2"]
strategy_instance = plugin(config)
```

---

## 11. Версионирование плагинов

Плагины должны иметь:

- semantic versioning (X.Y.Z),
- минимальную версию API,
- зависимость от версий движков.

Пример:

```yaml
api_version: "1.4+"
requires:
  - "engine.strategy>=2.0"
```

---

## 12. Hot Reload Plugins

Плагинная система поддерживает:

- hot-reload кода,
- отключение/подключение плагинов без остановки движков,
- обновление версий стратегий,
- динамическое переключение адаптеров.

Это важно для продакшена.

---

## 13. Плагины в продакшене

В реальном окружении плагинам нужны:

- CI/CD pipeline,
- тестирование и валидация,
- sandbox-защита,
- логирование действий,
- мониторинг.

---

## 14. Роль Plugin System в BotPlatform

Plugin System делает BotPlatform:

- расширяемой бесконечно,
- открытой для внешних разработчиков,
- безопасной,
- устойчивой к обновлениям,
- модульной,
- гибкой.

Плагинная система — основа большого экосистемного роста BotPlatform.
