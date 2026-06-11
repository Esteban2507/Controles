"""Módulo de procesamiento principal de datos."""
import time
import logging
import pandas as pd
from pathlib import Path
from utils.excel import read_excel_robust
from utils.validators import assert_cols, validate_excel_path, canonicalize
from utils.normalization import normalize_duplicates
from core.data_loader import DataLoader
from core.column_mapping import setup_arca_mapping, setup_cdp_mapping, robust_rename
from core.comparison import compare_data, generate_summary
from openpyxl.worksheet.table import Table, TableStyleInfo


logger = logging.getLogger(__name__)


def first_non_empty(series):
    """Devuelve el primer valor no vacío/no nulo de una serie."""
    for value in series:
        if pd.notna(value) and str(value).strip() != "":
            return value
    return series.iloc[0] if len(series) else pd.NA


def setup_aggregations(df):
    """Configura reglas de agregación genéricas (para CDP/E1/otros)."""
    agg_rules = {
        "amount_clean": lambda x: x.iloc[0],  # Cambiar a first para evitar duplicados en facturas con múltiples filas
        "currency_norm": "first",
        "vendor": "first",
        "issue_date": "first",
        "erp": "first",
    }

    if "CDP_line_count" in df.columns:
        agg_rules["CDP_line_count"] = "sum"
    if "E1_line_count" in df.columns:
        agg_rules["E1_line_count"] = "sum"

    if "doc_type" in df.columns:
        agg_rules["doc_type"] = "first"
    if "tipo_cambio" in df.columns:
        agg_rules["tipo_cambio"] = "first"
    if "invoice_number" in df.columns:
        agg_rules["invoice_number"] = first_non_empty
    if "posting_date_CDP" in df.columns:
        agg_rules["posting_date_CDP"] = "first"
    if "posting_date_E1" in df.columns:
        agg_rules["posting_date_E1"] = "first"

    return agg_rules


def aggregate_cdp_data(df_cdp):
    """Agrega datos CDP por Concatenado o nbr_doc."""
    if df_cdp.empty:
        return df_cdp

    df_cdp["CDP_line_count"] = 1
    agg_rules = setup_aggregations(df_cdp)

    # Asegurar que invoice_number se incluya si existe
    if "invoice_number" in df_cdp.columns and "invoice_number" not in agg_rules:
        agg_rules["invoice_number"] = "first"

    if "nbr_doc" in df_cdp.columns:
        agg_rules["Concatenado"] = "first"

        # Dividir entre con y sin nbr_doc
        df_cdp_valid = df_cdp[df_cdp["nbr_doc"].notna() & (df_cdp["nbr_doc"].astype(str).str.strip() != "")]
        df_cdp_miss = df_cdp[~(df_cdp["nbr_doc"].notna() & (df_cdp["nbr_doc"].astype(str).str.strip() != ""))]

        group_cols_valid = ["nbr_doc"]
        group_cols_miss = ["Concatenado"]
        if "posting_date_CDP" in df_cdp.columns and df_cdp["posting_date_CDP"].notna().any():
            group_cols_valid.append("posting_date_CDP")
            group_cols_miss.append("posting_date_CDP")

        # Agregar cada grupo
        df_g1 = df_cdp_valid.groupby(group_cols_valid, as_index=False).agg(agg_rules)
        df_g2 = df_cdp_miss.groupby(group_cols_miss, as_index=False).agg(agg_rules)

        return pd.concat([df_g1, df_g2], ignore_index=True)
    else:
        group_cols = ["Concatenado"]
        if "posting_date_CDP" in df_cdp.columns and df_cdp["posting_date_CDP"].notna().any():
            group_cols.append("posting_date_CDP")
        return df_cdp.groupby(group_cols, as_index=False).agg(agg_rules)


def aggregate_e1_data(df_e1):
    """Agrega datos E1 por Concatenado o nbr_doc."""
    if df_e1.empty:
        return df_e1

    df_e1["E1_line_count"] = 1
    agg_rules = setup_aggregations(df_e1)

    # Asegurar que invoice_number se incluya si existe
    if "invoice_number" in df_e1.columns and "invoice_number" not in agg_rules:
        agg_rules["invoice_number"] = "first"

    if "nbr_doc" in df_e1.columns:
        agg_rules["Concatenado"] = "first"

        # Dividir entre con y sin nbr_doc
        df_e1_valid = df_e1[df_e1["nbr_doc"].notna() & (df_e1["nbr_doc"].astype(str).str.strip() != "")]
        df_e1_miss = df_e1[~(df_e1["nbr_doc"].notna() & (df_e1["nbr_doc"].astype(str).str.strip() != ""))]

        group_cols_valid = ["nbr_doc"]
        group_cols_miss = ["Concatenado"]
        if "posting_date_E1" in df_e1.columns and df_e1["posting_date_E1"].notna().any():
            group_cols_valid.append("posting_date_E1")
            group_cols_miss.append("posting_date_E1")

        # Agregar cada grupo
        df_g1 = df_e1_valid.groupby(group_cols_valid, as_index=False).agg(agg_rules)
        df_g2 = df_e1_miss.groupby(group_cols_miss, as_index=False).agg(agg_rules)

        return pd.concat([df_g1, df_g2], ignore_index=True)
    else:
        group_cols = ["Concatenado"]
        if "posting_date_E1" in df_e1.columns and df_e1["posting_date_E1"].notna().any():
            group_cols.append("posting_date_E1")
        return df_e1.groupby(group_cols, as_index=False).agg(agg_rules)



def aggregate_arca_data(df_arca):
    """Agrega datos ARCA por Concatenado."""
    agg_arca = {
        "amount_clean": "sum",
        "currency_norm": "first",
        "vendor": "first",
        "issue_date": "first",
    }
    
    if "tipo" in df_arca.columns:
        agg_arca["tipo"] = "first"
    if "tipo_cambio" in df_arca.columns:
        agg_arca["tipo_cambio"] = "first"
    if "invoice_number_ARCA" in df_arca.columns:
        agg_arca["invoice_number_ARCA"] = first_non_empty
    
    return df_arca.groupby("Concatenado", as_index=False).agg(agg_arca)


def process_data(config, arca_path, cdp_path, e1_path="", fecha_filtro=None):
    """
    Procesa datos de ARCA y CDP/E1 generando reporte de diferencias.
    
    Args:
        config: Diccionario de configuración
        arca_path: Path a archivo ARCA
        cdp_path: Path a archivo CDP
        e1_path: Path a archivo E1 (no implementado)
        fecha_filtro: Fecha mínima para filtro CDP (datetime.date)
    
    Returns:
        tuple: (output_path, df_resumen, df_err)
    """
    
    print(f">>> Diagnóstico: {config.get('diagnostico', False)}")
    
    # === CRONÓMETRO ===
    t0 = time.perf_counter()
    
    # 1) Carga de datos
    loader = DataLoader(config)
    df_arca_raw = loader.load_arca(arca_path)
    df_cdp = loader.load_cdp(cdp_path, fecha_filtro)
    df_e1 = loader.load_e1(e1_path, fecha_filtro)

    
    # 2) Configurar mapeos
    print("3/8 Ajustando mapeos (Moneda/Monto) ...")
    map_arca = setup_arca_mapping(df_arca_raw, config)
    map_cdp = setup_cdp_mapping(df_cdp, config) if not df_cdp.empty else dict(config["columnas"]["CDP"])
    map_e1 = setup_cdp_mapping(df_e1, config, sheet_type="E1") if not df_e1.empty else dict(config.get("columnas", {}).get("E1", {}))

    
    # 3) Renombramiento robusto
    print("4/8 Renombrando columnas según YAML ...")
    req_base = ["Concatenado", "amount", "currency", "vendor", "issue_date", "duplicados"]
    df_arca_raw = robust_rename(df_arca_raw, map_arca, "ARCA", req_base)
    
    req_cdp = req_base.copy()
    if "doc_type" in map_cdp.values():
        req_cdp.append("doc_type")
    
    if not df_cdp.empty:
        df_cdp = robust_rename(df_cdp, map_cdp, "CDP", req_cdp)
        # Preservar invoice_number si existe
        for col in df_cdp.columns:
            if canonicalize(col) in ["invoicenumber", "numeroinvoice", "invoice_number", "numero_factura"]:
                if "invoice_number" not in df_cdp.columns:
                    df_cdp = df_cdp.rename(columns={col: "invoice_number"})
                break
    else:
        df_cdp = pd.DataFrame(columns=req_cdp)
    
    req_e1 = req_base.copy()
    if "doc_type" in map_e1.values():
        req_e1.append("doc_type")
    
    if not df_e1.empty:
        df_e1 = robust_rename(df_e1, map_e1, "E1", req_e1)
        # Preservar invoice_number si existe
        for col in df_e1.columns:
            if canonicalize(col) in ["invoicenumber", "numeroinvoice", "invoice_number", "numero_factura"]:
                if "invoice_number" not in df_e1.columns:
                    df_e1 = df_e1.rename(columns={col: "invoice_number"})
                break
    else:
        df_e1 = pd.DataFrame(columns=req_e1)
    
    # Validar columnas requeridas
    assert_cols(df_arca_raw, "ARCA", req_base)
    if not df_cdp.empty:
        assert_cols(df_cdp, "CDP", req_cdp)
    if not df_e1.empty:
        assert_cols(df_e1, "E1", req_e1)
    
    # 4) Preparar datos
    df_arca_raw = loader.prepare_arca(df_arca_raw)
    if not df_cdp.empty:
        df_cdp = loader.prepare_cdp(df_cdp)
    if not df_e1.empty:
        df_e1 = loader.prepare_e1(df_e1)
    
    if df_cdp.empty and df_e1.empty:
        print("ERROR: No se proporcionó ni CDP ni E1")
        raise ValueError("Debe proporcionar al menos un reporte (CDP o E1)")
    
    # 5) Calcular duplicados y comparar
    print("6/8 Calculando duplicados y comparando por Concatenado ...")
    df_reporte_all = pd.concat([df for df in [df_cdp, df_e1] if not df.empty], ignore_index=True, sort=False)
    universo_concat = set(df_reporte_all["Concatenado"].astype(str).unique())
    df_arca = df_arca_raw[df_arca_raw["Concatenado"].astype(str).isin(universo_concat)].copy()
    
    universo_dup = set(df_reporte_all["duplicados"].astype(str).unique())
    arca_dup_counts = df_arca_raw.groupby("duplicados").size().reset_index(name="ARCA_dup_count")
    arca_dup_counts = arca_dup_counts[arca_dup_counts["duplicados"].astype(str).isin(universo_dup)].copy()
    arca_dup_counts["EsDuplicado_ARCA"] = arca_dup_counts["ARCA_dup_count"] >= 2
    
    arca_count_by_key = dict(
        zip(arca_dup_counts["duplicados"].astype(str), arca_dup_counts["ARCA_dup_count"])
    )
    
    df_arca_g = aggregate_arca_data(df_arca)
    
    # 6) Comparar cada informe disponible
    print("7/8 Clasificando Status ...")
    tolerance = float(config.get("tolerancia_monto", 2.0))
    merge_frames = []
    
    if not df_cdp.empty:
        df_cdp_g = aggregate_cdp_data(df_cdp)
        cdp_keys_by_concat = (
            df_cdp.groupby("Concatenado")["duplicados"]
            .agg(lambda s: list(pd.unique(s)))
            .to_dict()
        )
        df_merge_cdp = compare_data(
            df_cdp_g,
            df_arca_g,
            tolerance,
            arca_dup_counts,
            cdp_keys_by_concat=cdp_keys_by_concat,
            arca_count_by_key=arca_count_by_key,
            report_type="CDP"
        )
        if not df_e1.empty:
            posibles_dup = (
                set(df_cdp["Concatenado"].astype(str).dropna().unique())
                & set(df_e1["Concatenado"].astype(str).dropna().unique())
            )
            if posibles_dup:
                mask = df_merge_cdp["Concatenado"].astype(str).isin(posibles_dup)
                df_merge_cdp.loc[mask, "Status"] = "Posible duplicado"
        df_merge_cdp["Fuente"] = "CDP"
        merge_frames.append(df_merge_cdp)
    
    if not df_e1.empty:
        df_e1_g = aggregate_e1_data(df_e1)
        e1_keys_by_concat = (
            df_e1.groupby("Concatenado")["duplicados"]
            .agg(lambda s: list(pd.unique(s)))
            .to_dict()
        )
        df_merge_e1 = compare_data(
            df_e1_g,
            df_arca_g,
            tolerance,
            arca_dup_counts,
            cdp_keys_by_concat=e1_keys_by_concat,
            arca_count_by_key=arca_count_by_key,
            report_type="E1"
        )
        if not df_cdp.empty:
            posibles_dup = (
                set(df_e1["Concatenado"].astype(str).dropna().unique())
                & set(df_cdp["Concatenado"].astype(str).dropna().unique())
            )
            if posibles_dup:
                mask = df_merge_e1["Concatenado"].astype(str).isin(posibles_dup)
                df_merge_e1.loc[mask, "Status"] = "Posible duplicado"
        df_merge_e1["Fuente"] = "E1"
        merge_frames.append(df_merge_e1)
    
    df_merge = pd.concat(merge_frames, ignore_index=True, sort=False)
    
    # Omitir registros faltantes en ARCA para el reporte final
    df_merge = df_merge[df_merge["Status"] != "Faltante en ARCA"].copy()
    
    df_resumen = generate_summary(df_merge)

    # Ajustes de columnas para el reporte
    if "vendor_ARCA" in df_merge.columns:
        df_merge = df_merge.drop(columns=["vendor_ARCA"])

    # Crear columna numero_factura desde reporte o ARCA
    if "numero_factura" not in df_merge.columns:
        df_merge["numero_factura"] = ""
    for report_type in ["E1", "CDP"]:
        invoice_col_reporte = f"invoice_number_{report_type}"
        if invoice_col_reporte in df_merge.columns:
            mask_empty = df_merge["numero_factura"] == ""
            df_merge.loc[mask_empty, "numero_factura"] = df_merge.loc[mask_empty, invoice_col_reporte].fillna("")
    if "invoice_number_ARCA" in df_merge.columns:
        mask_empty = df_merge["numero_factura"] == ""
        if mask_empty.any():
            df_merge.loc[mask_empty, "numero_factura"] = df_merge.loc[mask_empty, "invoice_number_ARCA"].fillna("")

    drop_invoice_cols = [c for c in ["invoice_number_CDP", "invoice_number_E1", "invoice_number", "invoice_number_ARCA"] if c in df_merge.columns]
    if drop_invoice_cols:
        df_merge = df_merge.drop(columns=drop_invoice_cols)

    # 8) Ordenar columnas
    cols_pref = [
        "Fuente", "posting_date_CDP", "posting_date_E1", "Status", "erp", "doc_type", "nbr_doc", "numero_factura",
        "Concatenado",
        "amount_clean_CDP", "currency_norm_CDP", "tipo_cambio_CDP", "issue_date_CDP", "vendor_CDP", "CDP_line_count",
        "amount_clean_E1", "currency_norm_E1", "tipo_cambio_E1", "issue_date_E1", "vendor_E1", "E1_line_count",
        "amount_clean_ARCA", "currency_norm_ARCA", "tipo_cambio_ARCA", "issue_date_ARCA",
        "ARCA_dup_count",
        "Diferencia_Monto",
    ]
    cols_final = [c for c in cols_pref if c in df_merge.columns] + [c for c in df_merge.columns if c not in cols_pref]
    df_merge = df_merge[cols_final]
    df_err = df_merge[df_merge["Status"] != "OK"].copy()
    
    # 9) Exportar
    print("8/8 Exportando a Excel (Formatos integrados)...")
    
    base_path_for_report = cdp_path if cdp_path else e1_path
    if not base_path_for_report:
        base_path_for_report = arca_path
    
    output_path = Path(base_path_for_report).parent / "Reporte_Control_Resultados.xlsx"
    
    if "nbr_doc" not in df_merge.columns:
        if "nbr_doc_CDP" in df_merge.columns and "nbr_doc_E1" not in df_merge.columns:
            df_merge = df_merge.rename(columns={"nbr_doc_CDP": "nbr_doc"})
        elif "nbr_doc_E1" in df_merge.columns and "nbr_doc_CDP" not in df_merge.columns:
            df_merge = df_merge.rename(columns={"nbr_doc_E1": "nbr_doc"})
        elif "nbr_doc_CDP" in df_merge.columns and "nbr_doc_E1" in df_merge.columns:
            df_merge["nbr_doc"] = df_merge["nbr_doc_CDP"].fillna(df_merge["nbr_doc_E1"])
    
    required_order = [
        "Fuente", "posting_date_CDP", "posting_date_E1", "Status", "erp", "doc_type", "nbr_doc", "numero_factura",
        "Concatenado", "amount_clean_CDP", "currency_norm_CDP", "tipo_cambio_CDP", "issue_date_CDP", "vendor_CDP", "CDP_line_count",
        "amount_clean_E1", "currency_norm_E1", "tipo_cambio_E1", "issue_date_E1", "vendor_E1", "E1_line_count",
        "amount_clean_ARCA", "currency_norm_ARCA", "tipo_cambio_ARCA", "issue_date_ARCA",
        "ARCA_dup_count", "Diferencia_Monto",
    ]
    
    for c in required_order:
        if c not in df_merge.columns:
            df_merge[c] = pd.NA
    
    df_current_baseline = df_merge[required_order].copy()
    for col in ["posting_date_CDP", "posting_date_E1"]:
        if col in df_current_baseline.columns:
            df_current_baseline[col] = df_current_baseline[col].astype(str)
    
    run_ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    if output_path.exists():
        try:
            df_existing = pd.read_excel(output_path, sheet_name="Detalle Completo", engine="openpyxl")
        except Exception:
            df_existing = pd.DataFrame()
    else:
        df_existing = pd.DataFrame()
    
    if not df_existing.empty:
        for col in ["posting_date_CDP", "posting_date_E1"]:
            if col not in df_existing.columns:
                df_existing[col] = ""
            else:
                df_existing[col] = df_existing[col].astype(str)
        if "Fuente" not in df_existing.columns:
            df_existing["Fuente"] = ""
        if "Concatenado" not in df_existing.columns:
            df_existing["Concatenado"] = ""
    
    if df_existing.empty:
        df_out = df_current_baseline
    else:
        key_cols = []
        if "Fuente" in df_existing.columns and "Fuente" in df_current_baseline.columns:
            key_cols.append("Fuente")
        if "Concatenado" in df_existing.columns and "Concatenado" in df_current_baseline.columns:
            key_cols.append("Concatenado")
        version_cols = [c for c in required_order if c not in key_cols]
        df_version = df_current_baseline.rename(columns={c: f"{c}_{run_ts}" for c in version_cols})
        if key_cols:
            df_out = pd.merge(df_existing, df_version, on=key_cols, how="outer")
        else:
            df_out = pd.concat([df_existing, df_version], ignore_index=True, sort=False)
    
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_out.to_excel(writer, sheet_name="Detalle Completo", index=False)
        df_err.to_excel(writer, sheet_name="Errores y Faltantes", index=False)
        
        ws_detalle = writer.sheets["Detalle Completo"]
        table = Table(displayName="DetalleCompleto", ref=ws_detalle.dimensions)
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        ws_detalle.add_table(table)
        for col in ws_detalle.columns:
            max_len = 0
            letter = col[0].column_letter
            for cell in col:
                try:
                    max_len = max(max_len, len(str(cell.value)))
                except Exception:
                    pass
            ws_detalle.column_dimensions[letter].width = min((max_len + 2) * 1.1, 60)
    
    # Cronómetro
    t_elapsed = time.perf_counter() - t0
    exec_msg = f"{t_elapsed:.2f}s"
    
    return str(output_path), df_resumen, df_err
