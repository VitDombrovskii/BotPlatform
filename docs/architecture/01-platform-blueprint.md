# Пункт A — Глобальная архитектурная схема BotPlatform

## 1. Общая концепция платформы
BotPlatform — это многоуровневая алготрейдинговая система со следующими целями:

- Поддержка нескольких бирж  
- Поддержка нескольких стратегий  
- Возможность масштабирования  
- Возможность распределённых движков  
- Чёткое разделение ответственности  
- Независимость стратегий от инфраструктуры  
- Событийная архитектура  

## 2. Уровни архитектуры

```
                 +---------------------+
                 |  Пользователи (UI)  |
                 +---------------------+
                            │
                            ▼
                 +---------------------+
                 | Notifications Layer |
                 | Telegram / Email    |
                 +---------------------+
                            │
                            ▼
                 +---------------------+
                 |  Monitoring Layer   |
                 | Web Dashboard, Logs |
                 +---------------------+
                            │
                            ▼
                 +---------------------+
                 |  Strategy Layer     |
                 |  (мозг системы)     |
                 +---------------------+
                            │
                            ▼
                 +---------------------+
                 |   Engines Layer     |
                 | market / signals /  |
                 | strategies / exec   |
                 +---------------------+
                            │
                            ▼
                 +---------------------+
                 |   Exchange Layer    |
                 | Binance, BingX, OKX |
                 +---------------------+
                            │
                            ▼
                 +---------------------+
                 |   Network / APIs    |
                 +---------------------+
```

## 3. Основные модули BotPlatform

### 3.1 Exchange Layer
- Унифицированный интерфейс работы с биржами  
- Приведение данных к единому виду  
- Исполнение ордеров  

### 3.2 Engines Layer
- MarketDataEngine  
- SignalsEngine  
- StrategyEngine  
- ExecutionEngine  

### 3.3 Strategies Layer
- Логика стратегий  
- Legs  
- Risk-модули  

### 3.4 Leg Engine
- PnL  
- scale-in  
- scale-out  
- bubble logic  
- сериализация состояния  

### 3.5 Signals Layer
- Индикаторы  
- Orderflow  
- OI  
- Комбинированные сигналы  

### 3.6 Storage Layer
- Стейты  
- История сигналов  
- Ордеры  
- Логи  

### 3.7 Event Bus
- Централизованная шина событий  

### 3.8 Monitoring / Logging
- Дашборд  
- Метрики  
- Логи  

### 3.9 Notifications Layer
- Телеграм / Email  

## 4. Потоки данных в системе

```
Exchange → MarketDataEngine → EventBus → SignalsEngine → EventBus →
→ StrategyEngine → Strategies → EventBus → ExecutionEngine → Exchange
```

Параллельно:

```
EventBus → Monitoring / Logging → UI / Telegram
```

## 5. Базовые принципы

- Стратегия независима от бирж  
- Биржи независимы от стратегий  
- Движки независимы от стратегий  
- Коммуникация через события  
- Лёгкое масштабирование  

## 6. Дерево директорий

```
BotPlatform/
├── exchanges/
├── engines/
├── strategies/
│   └── hedge_v2/
│       ├── leg/
│       ├── engine.py
│       ├── config.py
│       └── strategy.py
├── signals/
├── storage/
├── core/
├── monitoring/
├── notifications/
├── admin/
└── main.py
```
