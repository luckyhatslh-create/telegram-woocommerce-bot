import os
from dataclasses import dataclass
from typing import Literal

QualityMode = Literal["preview", "hq"]


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name)
    if value is None:
        return default if default is not None else ""
    return value


def get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


@dataclass
class ProviderSettings:
    anthropic_api_key: str = get_env("ANTHROPIC_API_KEY", "")
    replicate_api_token: str = get_env("REPLICATE_API_TOKEN", "")
    flux_base_model: str = get_env("FLUX_BASE_MODEL", "black-forest-labs/flux-schnell")
    flux_fill_model: str = get_env("FLUX_FILL_MODEL", "black-forest-labs/flux-fill-pro")


@dataclass
class PipelineSettings:
    quality_mode: QualityMode = "preview"
    max_size: int = get_int("MAX_SIZE", 512)
    steps_preview: int = get_int("STEPS_PREVIEW", 20)
    steps_hq: int = get_int("STEPS_HQ", 35)
    timeout_seconds: int = get_int("PIPELINE_TIMEOUT", 90)
    retries: int = get_int("PIPELINE_RETRIES", 1)


@dataclass
class TelegramSettings:
    token: str = get_env("TELEGRAM_BOT_TOKEN", "")


@dataclass
class AppConfig:
    providers: ProviderSettings = ProviderSettings()
    pipeline: PipelineSettings = PipelineSettings()
    telegram: TelegramSettings = TelegramSettings()


CONFIG = AppConfig()
