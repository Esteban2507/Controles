import pandas as pd
import pytest
from core.comparison import compare_data


def test_compare_data_tipo_cambio_ok():
    df_cdp_g = pd.DataFrame([
        {
            "Concatenado": "X1",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": 1.0,
        }
    ])
    df_arca_g = pd.DataFrame([
        {
            "Concatenado": "X1",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": 1.0,
        }
    ])
    arca_dup_counts = pd.DataFrame([{"duplicados": "K1", "ARCA_dup_count": 1}])
    cdp_keys_by_concat = {"X1": ["K1"]}
    arca_count_by_key = {"K1": 1}

    df_merge = compare_data(df_cdp_g, df_arca_g, tolerance=2.0,
                            arca_dup_counts=arca_dup_counts,
                            cdp_keys_by_concat=cdp_keys_by_concat,
                            arca_count_by_key=arca_count_by_key)

    assert df_merge.loc[0, "Status"] == "OK"


def test_compare_data_tipo_cambio_error():
    df_cdp_g = pd.DataFrame([
        {
            "Concatenado": "X2",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": 10.5,
        }
    ])
    df_arca_g = pd.DataFrame([
        {
            "Concatenado": "X2",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": 9.0,
        }
    ])
    arca_dup_counts = pd.DataFrame([{"duplicados": "K2", "ARCA_dup_count": 1}])
    cdp_keys_by_concat = {"X2": ["K2"]}
    arca_count_by_key = {"K2": 1}

    df_merge = compare_data(df_cdp_g, df_arca_g, tolerance=2.0,
                            arca_dup_counts=arca_dup_counts,
                            cdp_keys_by_concat=cdp_keys_by_concat,
                            arca_count_by_key=arca_count_by_key)

    assert df_merge.loc[0, "Status"] == "Error de Tipo Cambio"


def test_compare_data_e1_ignores_tipo_cambio():
    df_e1_g = pd.DataFrame([
        {
            "Concatenado": "X6",
            "amount_clean": 100.0,
            "currency_norm": "USD",
            "tipo_cambio": 5.0,
        }
    ])
    df_arca_g = pd.DataFrame([
        {
            "Concatenado": "X6",
            "amount_clean": 100.0,
            "currency_norm": "USD",
            "tipo_cambio": 1.0,
        }
    ])
    arca_dup_counts = pd.DataFrame([{"duplicados": "K6", "ARCA_dup_count": 1}])
    cdp_keys_by_concat = {"X6": ["K6"]}
    arca_count_by_key = {"K6": 1}

    df_merge = compare_data(df_e1_g, df_arca_g, tolerance=2.0,
                            arca_dup_counts=arca_dup_counts,
                            cdp_keys_by_concat=cdp_keys_by_concat,
                            arca_count_by_key=arca_count_by_key,
                            report_type="E1")

    assert df_merge.loc[0, "Status"] == "OK"


def test_compare_data_tipo_cambio_ignored_when_local_currency():
    df_cdp_g = pd.DataFrame([
        {
            "Concatenado": "X3",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": 1.0,
        }
    ])
    df_arca_g = pd.DataFrame([
        {
            "Concatenado": "X3",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": 1.5,
        }
    ])
    arca_dup_counts = pd.DataFrame([{"duplicados": "K3", "ARCA_dup_count": 1}])
    cdp_keys_by_concat = {"X3": ["K3"]}
    arca_count_by_key = {"K3": 1}

    df_merge = compare_data(df_cdp_g, df_arca_g, tolerance=2.0,
                            arca_dup_counts=arca_dup_counts,
                            cdp_keys_by_concat=cdp_keys_by_concat,
                            arca_count_by_key=arca_count_by_key)

    assert df_merge.loc[0, "Status"] == "OK"


@pytest.mark.parametrize("local_rate", [0.0, 0.5, 1.0, 1.5, 2.0])
def test_compare_data_tipo_cambio_ignored_for_local_currency_rates(local_rate):
    df_cdp_g = pd.DataFrame([
        {
            "Concatenado": "X4",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": local_rate,
        }
    ])
    df_arca_g = pd.DataFrame([
        {
            "Concatenado": "X4",
            "amount_clean": 100.0,
            "currency_norm": "ARS",
            "tipo_cambio": 1.5,
        }
    ])
    arca_dup_counts = pd.DataFrame([{"duplicados": "K4", "ARCA_dup_count": 1}])
    cdp_keys_by_concat = {"X4": ["K4"]}
    arca_count_by_key = {"K4": 1}

    df_merge = compare_data(df_cdp_g, df_arca_g, tolerance=2.0,
                            arca_dup_counts=arca_dup_counts,
                            cdp_keys_by_concat=cdp_keys_by_concat,
                            arca_count_by_key=arca_count_by_key)

    assert df_merge.loc[0, "Status"] == "OK"


def test_compare_data_tipo_cambio_with_rounding_and_tolerance():
    df_cdp_g = pd.DataFrame([
        {
            "Concatenado": "X5",
            "amount_clean": 100.0,
            "currency_norm": "USD",
            "tipo_cambio": "10.1234567890",
        }
    ])
    df_arca_g = pd.DataFrame([
        {
            "Concatenado": "X5",
            "amount_clean": 100.0,
            "currency_norm": "USD",
            "tipo_cambio": "10.6200000000",
        }
    ])
    arca_dup_counts = pd.DataFrame([{"duplicados": "K5", "ARCA_dup_count": 1}])
    cdp_keys_by_concat = {"X5": ["K5"]}
    arca_count_by_key = {"K5": 1}

    df_merge = compare_data(df_cdp_g, df_arca_g, tolerance=2.0,
                            arca_dup_counts=arca_dup_counts,
                            cdp_keys_by_concat=cdp_keys_by_concat,
                            arca_count_by_key=arca_count_by_key)

    assert df_merge.loc[0, "Status"] == "OK"
