"""
Entry point for BotPlatform.

На этом этапе main.py — минимальный загрузчик, который просто проверяет,
что пакет устанавливается и импортируется без ошибок.
"""

from botplatform.utils.logging import configure_logging


def main() -> None:
    logger = configure_logging("botplatform.main")
    logger.info("BotPlatform skeleton initialized")
    # Здесь в будущем будет запуск EventBus, движков и стратегий.


if __name__ == "__main__":
    main()
