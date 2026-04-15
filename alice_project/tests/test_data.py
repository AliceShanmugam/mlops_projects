"""
Tests de validation des données raw.
"""

import pytest
import pandas as pd


def test_sample_df_no_missing_values(sample_df):
    """Les colonnes clés n'ont pas de valeurs manquantes."""
    for col in ["designation", "productid", "prdtypecode"]:
        assert sample_df[col].isnull().sum() == 0


def test_sample_df_has_expected_columns(sample_df):
    expected = {"designation", "description", "productid", "imageid", "prdtypecode"}
    assert expected.issubset(set(sample_df.columns))


def test_prdtypecode_values_are_known(sample_df):
    """Tous les prdtypecode sont dans les codes connus du LABEL_MAPPING."""
    from src.preprocessing.preprocessing import LABEL_MAPPING
    known_codes = {code for codes in LABEL_MAPPING.values() for code in codes}
    unknown = set(sample_df["prdtypecode"]) - known_codes
    assert len(unknown) == 0, f"Codes inconnus : {unknown}"


def test_productid_unique(sample_df):
    assert sample_df["productid"].is_unique