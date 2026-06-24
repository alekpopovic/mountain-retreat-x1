"""Data-driven localization helpers for generated visible text."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SUPPORTED_LANGUAGES = ("sr-Latn", "en")
DEFAULT_LANGUAGE = "sr-Latn"
DEFAULT_LOCALIZATION_DIR = Path("data/localization")


class LocalizationError(ValueError):
    """Raised when localization data cannot be loaded."""


@dataclass(frozen=True)
class Translator:
    """Translate configured visible strings without changing code identifiers."""

    language: str
    data: dict[str, Any]

    def text(self, key: str, default: str | None = None) -> str:
        value = self.data.get(key, default)
        if isinstance(value, str):
            return value
        if default is not None:
            return default
        return key

    def mapping(self, key: str) -> dict[str, str]:
        value = self.data.get(key, {})
        if not isinstance(value, dict):
            return {}
        return {str(item_key): str(item_value) for item_key, item_value in value.items()}

    def list_text(self, key: str) -> list[str]:
        value = self.data.get(key, [])
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    def translate_mapping_value(self, mapping_key: str, value: str) -> str:
        return self.mapping(mapping_key).get(value, value)


def normalize_language(language: str | None) -> str:
    """Return a supported language code, defaulting to Serbian Latin."""
    if language is None or not language.strip():
        return DEFAULT_LANGUAGE
    normalized = language.strip()
    if normalized not in SUPPORTED_LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES)
        raise LocalizationError(f"Unsupported language '{language}'. Supported: {supported}.")
    return normalized


def load_translator(
    language: str | None = None,
    localization_dir: Path = DEFAULT_LOCALIZATION_DIR,
) -> Translator:
    """Load localization YAML for a supported language."""
    normalized = normalize_language(language)
    path = localization_dir / f"{normalized}.yaml"
    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise LocalizationError(f"Missing localization file: {path}") from exc
    except yaml.YAMLError as exc:
        raise LocalizationError(f"Invalid localization YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise LocalizationError(f"Localization file must contain a mapping: {path}")
    file_language = data.get("language")
    if file_language != normalized:
        raise LocalizationError(
            f"Localization file {path} declares language {file_language!r}, "
            f"expected {normalized!r}."
        )
    return Translator(language=normalized, data=data)
