# config_bingx_example.py
# Конфигурационный файл для работы с BingX Testnet

# --- API ключи (вставь свои) ---
BINGX_API_KEY = "0OgeqvU9JsDBjTKsd1mkEYqwbyLJiQ5yVTaevLlScgXzTR9sVGN9rjnKOL1hdcIGZ0yj3NRGz1VvqAvo5LzA"
BINGX_API_SECRET = "xom89fzyyXrfvDn8HSD8LxyW2Bjq6mKN2syEHrBATDqsHVKWYAUJ1joWMJLOBVBz0foulvmsZAMt9hkZMNAcg"

# --- REST API Base URL (testnet) ---
# Если твой старый проект использовал open-api-vst.bingx.com — оставь так.
BINGX_REST_BASE_URL = "https://open-api-vst.bingx.com"

# --- WebSocket Market Stream URL ---
# !!! ВАЖНО: замени на реальный Testnet WS URL из документации !!!
# Пример:
#   wss://open-api-swap.bingx.com/stream
#   wss://open-api-test.bingx.com/market
# (у Testnet свои домены — подставь свой)
BINGX_WS_MARKET_URL = "wss://open-api-swap.bingx.com/stream"
