"""
Tests des fonctions de preprocessing.
"""

import pytest
from src.preprocessing.preprocessing import clean_text, detect_language, LABEL_MAPPING


def test_clean_text_removes_html():
    result = clean_text("<b>Chaussures</b> &amp; sport")
    assert "<b>" not in result
    assert "&amp;" not in result
    assert "chaussures" in result


def test_clean_text_lowercases():
    result = clean_text("CHAUSSURES Nike")
    assert result == result.lower()


def test_clean_text_handles_empty():
    result = clean_text("")
    assert isinstance(result, str)


def test_detect_language_french():
    lang = detect_language("Chaussures de sport pour homme")
    assert lang == "fr"


def test_detect_language_unknown_on_empty():
    lang = detect_language("")
    assert lang == "unknown"


def test_label_mapping_covers_all_labels():
    """Vérifie que LABEL_MAPPING couvre les labels 0-7 sans doublon."""
    all_codes = []
    for label, codes in LABEL_MAPPING.items():
        assert 0 <= label <= 7
        all_codes.extend(codes)
    # Pas de code dupliqué entre les labels
    assert len(all_codes) == len(set(all_codes))


def test_label_mapping_has_8_classes():
    assert len(LABEL_MAPPING) == 8