from __future__ import annotations
import json, os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class BingXConfig:
    api_key: str
    api_secret: str
    rest_url: str
    ws_market_url: str
    symbols: list[str]

@dataclass
class PlatformConfig:
    mode: str

class ConfigManager:
    def __init__(self):
        self._load_env()
        self.mode = os.getenv("PLATFORM_MODE", "mock").lower()
        self._load_mode_json()

        self.bingx = BingXConfig(
            api_key=os.getenv("BINGX_API_KEY", ""),
            api_secret=os.getenv("BINGX_API_SECRET", ""),
            rest_url=self._env_json["bingx"]["rest_url"],
            ws_market_url=self._env_json["bingx"]["ws_market_url"],
            symbols=self._env_json["bingx"]["symbols"],
        )
        self.platform = PlatformConfig(self.mode)

    def _load_env(self):
        env_path = Path(__file__).resolve().parent.parent / "secrets.env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            print("[ConfigManager] WARNING: secrets.env not found.")

    def _load_mode_json(self):
        json_path = Path(__file__).resolve().parent / "environments" / f"{self.mode}.json"
        if not json_path.exists():
            raise RuntimeError(f"Config file not found: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            self._env_json = json.load(f)
