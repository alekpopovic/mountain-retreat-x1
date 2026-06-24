import pytest

from mountain_retreat_x1.localization import LocalizationError, load_translator, normalize_language


def test_load_serbian_latin_translator_returns_disclaimer() -> None:
    translator = load_translator("sr-Latn")

    assert translator.language == "sr-Latn"
    assert "PRELIMINARNI planski dokument" in translator.text("disclaimer_text")
    assert translator.translate_mapping_value("room_names", "kitchen") == "kuhinja"


def test_load_english_translator_returns_english_disclaimer() -> None:
    translator = load_translator("en")

    assert translator.language == "en"
    assert "Preliminary planning document only" in translator.text("disclaimer_text")


def test_unsupported_language_raises_clear_error() -> None:
    with pytest.raises(LocalizationError, match="Unsupported language"):
        normalize_language("sr-Cyrl")
