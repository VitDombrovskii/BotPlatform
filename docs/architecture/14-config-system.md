
# 14-config-system.md — Система конфигураций (Config System) в BotPlatform

## 1. Назначение Config System

Config System — единый механизм управления всеми параметрами платформы:

- параметры движков (частота тиков, адаптеры, лимиты),
- параметры стратегий (пороговые значения, режимы, таймфреймы),
- параметры соединений с биржами,
- параметры пользователей и аккаунтов,
- параметры логирования, уведомлений, storage,
- чувствительные данные (API-ключи, токены).

Config System делает платформу:
- предсказуемой,
- гибкой,
- безопасной,
- удобной для масштабирования,
- легко управляемой на продакшене.

---

## 2. Общая архитектура Config System

```
ConfigSystem
├── ConfigLoader
├── ConfigValidator
├── ConfigSchema
├── SecretsVault
└── LiveConfigManager
```

---

## 3. Формат конфигураций

### 3.1 YAML как основной формат

Причины:
- легко читается,
- хорошо документируется,
- поддерживает вложенность,
- прост для CI/CD,
- подходит для генерации кода.

Пример:

```yaml
engines:
  market:
    update_interval_ms: 100
    sources:
      - binance
      - bingx

strategy:
  hedge_leg:
    enabled: true
    base_size: 0.01
    bubble:
      enabled: true
      max_levels: 4
      step_pct: 0.5
      scale_factor: 1.7
```

---

## 4. ConfigLoader

Задачи:

- загрузка YAML/JSON из:
  - локальных файлов,
  - удалённых конфигов (S3, Git, API),
  - переменных окружения,
  - секрет-хранилищ (Vault/KMS).
- объединение в единый config tree,
- механизм `defaults + overrides`.

### 4.1 Порядок загрузки

```
1. default.yaml
2. env.yaml (dev/prod/test)
3. secrets
4. runtime overrides (через API/UI)
```

---

## 5. ConfigSchema

ConfigSchema — JSONSchema/Pydantic-модель, определяющая структуру:

```python
class StrategyConfig(BaseModel):
    enabled: bool
    base_size: float
    bubble: BubbleConfig
```

Цель:
- типизация,
- валидация,
- автодокументация,
- защита от неверных параметров.

---

## 6. ConfigValidator

Проверяет:
- типы данных,
- диапазоны значений,
- обязательные поля,
- корректность режимов,
- согласованность параметров (например: bubble.max_levels ≥ 1).

При ошибке:
```
system.error (source="config", message="Invalid config")
```

---

## 7. Структура основной иерархии конфигураций

```
config/
├── engines/
│   ├── market.yaml
│   ├── signals.yaml
│   ├── strategy.yaml
│   └── execution.yaml
├── strategies/
│   ├── hedge_leg.yaml
│   ├── grid_beta.yaml
│   └── scalper_x.yaml
├── storage.yaml
├── logging.yaml
├── notifications.yaml
└── connections.yaml
```

---

## 8. Связь Config System и движков

### MarketDataEngine
- интервалы обновления,
- источники,
- WS/REST режим,
- фильтры данных.

### SignalsEngine
- активные сигналы,
- параметры отдельных индикаторов.

### StrategyEngine
- привязка стратегий,
- параметры исполнения,
- риск-менеджмент.

### ExecutionEngine
- тип ордеров,
- задержки,
- лимиты.

---

## 9. Конфигурации стратегий

Стратегия должна получать свой под-конфиг:

```yaml
strategy:
  hedge_leg:
    base_size: 0.01
    scale_factor: 1.6
    bubble:
      enabled: true
      levels: 4
```

Strategy Engine автоматически передаёт его в стратегию:

```python
strategy = HedgeLegStrategy(config=strategy_config)
```

---

## 10. Хранение чувствительных данных (SecretsVault)

Config System не хранит API-ключи в открытом виде.

SecretsVault может быть:
- Hashicorp Vault,
- AWS KMS,
- GCP Secret Manager,
- локальное хранилище с шифрованием.

Хранит:
- API key,
- API secret,
- webhook tokens,
- OAuth токены.

Ключи загружаются при старте:

```yaml
connections:
  binance:
    api_key: ${vault:binance.api_key}
    api_secret: ${vault:binance.api_secret}
```

---

## 11. LiveConfigManager — горячее изменение конфигов

Поддержка live-reloading:

- Market Engine может менять частоту обновления,
- Strategy Engine может менять параметры стратегий,
- Signals Engine может включать/выключать модули сигналов,
- Execution Engine может менять лимиты.

Runtime изменение конфигов публикует:

```
system.config_reload
```

Стратегии и движки получают уведомления через EventBus.

---

## 12. Версионирование конфигов

Config System должен поддерживать:

- версии стратегий,
- версии движков,
- миграции параметров,
- откат к предыдущей версии.

Это важно для продакшена.

---

## 13. Роль Config System в BotPlatform

Config System обеспечивает:

- гибкость развития,
- лёгкость управления,
- безопасность хранения ключей,
- масштабируемость,
- удобство CI/CD,
- контроль всех параметров платформы без изменения кода.

Config System — это «орган управления» всей BotPlatform.
