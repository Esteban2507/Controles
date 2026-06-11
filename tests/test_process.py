import pandas as pd
from pathlib import Path
from utils.config import load_config
from core.process import process_data


def _write_excel(path, sheet_name, df):
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)


def test_process_data_with_only_e1(tmp_path):
    config = load_config()
    config["refresh_before_read"] = False

    arca_df = pd.DataFrame([
        {
            "Concatenado": "A123",
            "Fecha": "2026-01-01",
            "Proveedor": "Proveedor X",
            "Moneda": "USD",
            "Monto": 100,
            "duplicados": "D1",
        }
    ])

    e1_df = pd.DataFrame([
        {
            "Concatenado.E1": "A123",
            "Fecha Emision": "2026-01-01",
            "Tipo de doc": "Factura",
            "Proveedor": "Proveedor X",
            "Moneda": "USD",
            "Monto": 100,
            "duplicados": "D1",
        }
    ])

    arca_path = tmp_path / "arca.xlsx"
    e1_path = tmp_path / "e1.xlsx"
    _write_excel(arca_path, "AFIP", arca_df)
    _write_excel(e1_path, "E1", e1_df)

    output_path, df_resumen, df_err = process_data(
        config,
        str(arca_path),
        "",
        str(e1_path),
        None,
    )

    assert Path(output_path).exists()
    assert not df_err.empty is False
    assert "E1" in df_resumen.columns or "Status" in df_resumen.columns


def test_process_data_e1_uses_concatenado_e1_as_duplicados(tmp_path):
    config = load_config()
    config["refresh_before_read"] = False

    arca_df = pd.DataFrame([
        {
            "Concatenado": "A123",
            "Fecha": "2026-01-01",
            "Proveedor": "Proveedor X",
            "Moneda": "USD",
            "Monto": 100,
            "duplicados": "A123",
        }
    ])

    e1_df = pd.DataFrame([
        {
            "Concatenado.E1": "A123",
            "Fecha Emision": "2026-01-01",
            "Tipo de doc": "Factura",
            "Proveedor": "Proveedor X",
            "Moneda": "USD",
            "Monto": 100,
        }
    ])

    arca_path = tmp_path / "arca.xlsx"
    e1_path = tmp_path / "e1.xlsx"
    _write_excel(arca_path, "AFIP", arca_df)
    _write_excel(e1_path, "E1", e1_df)

    output_path, df_resumen, df_err = process_data(
        config,
        str(arca_path),
        "",
        str(e1_path),
        None,
    )

    assert Path(output_path).exists()
    assert not df_err.empty is False
    assert "OK" in df_resumen["Status"].values or "Status" in df_resumen.columns


def test_process_data_with_cdp_and_e1(tmp_path):
    config = load_config()
    config["refresh_before_read"] = False

    arca_df = pd.DataFrame([
        {
            "Concatenado": "B123",
            "Fecha": "2026-01-02",
            "Proveedor": "Proveedor Y",
            "Moneda": "ARS",
            "Monto": 200,
            "duplicados": "D2",
        }
    ])

    cdp_df = pd.DataFrame([
        {
            "Concatenado": "B123",
            "Fecha Emision": "2026-01-02",
            "Tipo de doc": "Factura",
            "Proveedor": "Proveedor Y",
            "Moneda": "ARS",
            "Monto": 200,
            "duplicados": "D2",
        }
    ])

    e1_df = pd.DataFrame([
        {
            "Concatenado.E1": "B123",
            "Fecha Emision": "2026-01-02",
            "Tipo de doc": "Factura",
            "Proveedor": "Proveedor Y",
            "Moneda": "ARS",
            "Monto": 200,
            "duplicados": "D2",
        }
    ])

    arca_path = tmp_path / "arca.xlsx"
    cdp_path = tmp_path / "cdp.xlsx"
    e1_path = tmp_path / "e1.xlsx"
    _write_excel(arca_path, "AFIP", arca_df)
    _write_excel(cdp_path, "CDP", cdp_df)
    _write_excel(e1_path, "E1", e1_df)

    output_path, df_resumen, df_err = process_data(
        config,
        str(arca_path),
        str(cdp_path),
        str(e1_path),
        None,
    )

    assert Path(output_path).exists()
    df_out = pd.read_excel(output_path, sheet_name="Detalle Completo", engine="openpyxl")
    assert set(df_out["Fuente"].dropna().unique()) == {"CDP", "E1"}
