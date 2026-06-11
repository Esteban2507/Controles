"""Módulo de mapeo robusto de columnas."""
import pandas as pd
import logging
from utils.validators import canonicalize, assert_cols, ValidationError
from utils.normalization import remove_mapping_by_value
from core.column_detection import select_best_amount, select_best_currency
from exceptions import ColumnMappingError


logger = logging.getLogger(__name__)


def robust_rename(df: pd.DataFrame, mapping: dict, sistema: str, required_cols: list) -> pd.DataFrame:
    """
    Renombra columnas de forma robusta usando mapeo flexible.
    
    Args:
        df: DataFrame a renombrar
        mapping: Diccionario {columna_original: columna_nueva}
        sistema: Nombre del sistema (para logging)
        required_cols: Columnas que deben existir después del rename
    
    Returns:
        DataFrame con columnas renombradas
    """
    # Crear mapeo canónico
    canon_map = {canonicalize(k): v for k, v in mapping.items()}
    
    # Generar renombramiento
    out_rename = {}
    for col in df.columns:
        c = canonicalize(col)
        if c in canon_map:
            destino = canon_map[c]
            if isinstance(destino, list):
                # Primero renombrar a la primera columna y luego copiar el resto
                if destino[0] not in out_rename.values():
                    out_rename[col] = destino[0]
            else:
                # Evitar duplicados
                if destino in out_rename.values():
                    continue
                out_rename[col] = destino
    
    df = df.rename(columns=out_rename)
    original_columns = list(out_rename.keys())

    # Copiar columnas adicionales definidas en los mapeos listados
    for col in original_columns:
        destino = canon_map[canonicalize(col)]
        if isinstance(destino, list) and len(destino) > 1:
            source_col = out_rename.get(col, col)
            if source_col not in df.columns:
                continue
            for extra_dest in destino[1:]:
                if extra_dest not in df.columns:
                    df[extra_dest] = df[source_col]
    
    # Heurística: detectar columna "duplicados"
    if "duplicados" in required_cols and "duplicados" not in df.columns:
        candidates = []
        for col in df.columns:
            c = canonicalize(col)
            if any(p in c for p in ["duplic", "ctrldupli", "concatenadomonto", "concatenadomasmonto"]):
                candidates.append(col)
        
        if len(candidates) == 1:
            df = df.rename(columns={candidates[0]: "duplicados"})
            logger.info(f"[{sistema}] 'duplicados' por heurística: {candidates[0]}")
        elif len(candidates) > 1:
            elegido = max(candidates, key=len)
            df = df.rename(columns={elegido: "duplicados"})
            logger.warning(f"[{sistema}] 'duplicados' múltiples {candidates}. Usado: {elegido}")
    
    # Heurística: detectar columna "vendor"
    if "vendor" in required_cols and "vendor" not in df.columns:
        candidates = []
        for col in df.columns:
            c = canonicalize(col)
            if any(p in c for p in ["receptor", "proveedor", "vendor", "denominacion"]):
                candidates.append(col)
        
        if len(candidates) == 1:
            df = df.rename(columns={candidates[0]: "vendor"})
            logger.info(f"[{sistema}] 'vendor' por heurística: {candidates[0]}")
        elif len(candidates) > 1:
            elegido = max(candidates, key=len)
            df = df.rename(columns={elegido: "vendor"})
            logger.warning(f"[{sistema}] 'vendor' múltiples {candidates}. Usado: {elegido}")
    
    # Validar columnas requeridas
    try:
        assert_cols(df, sistema, required_cols)
    except ValidationError as e:
        logger.error(str(e))
        raise
    
    return df


def setup_arca_mapping(df_arca_raw: pd.DataFrame, config: dict) -> dict:
    """Configura mapeo de columnas ARCA con detección automática."""
    mapping = dict(config["columnas"]["ARCA"])
    
    # Detectar mejor moneda
    best_currency = select_best_currency(df_arca_raw)
    if best_currency:
        mapping = remove_mapping_by_value(mapping, "currency")
        mapping[best_currency] = "currency"
    
    # ARCA siempre usa columna "Monto" para amount
    mapping = remove_mapping_by_value(mapping, "amount")
    mapping["Monto"] = "amount"
    
    # Buscar columna de Número de Factura en ARCA (ej: Número Hasta)
    for col in df_arca_raw.columns:
        col_canon = canonicalize(col)
        if any(p in col_canon for p in ["numero", "número", "nro", "factura", "hasta", "invoice"]):
            if "invoice_number" not in mapping.values():
                mapping[col] = "invoice_number_ARCA"
                logger.debug(f"Mapeo ARCA: {col} -> invoice_number_ARCA")
                break
    
    return mapping


def setup_cdp_mapping(df_cdp: pd.DataFrame, config: dict, sheet_type: str = "CDP") -> dict:
    """Configura mapeo de columnas CDP/E1 con detección automática."""
    mapping = dict(config["columnas"].get(sheet_type, config["columnas"]["CDP"]))
    
    if df_cdp.empty:
        return mapping
    
    # CDP/E1: preferir "Monto total" si existe
    if "Monto total" in df_cdp.columns:
        mapping = remove_mapping_by_value(mapping, "amount")
        mapping["Monto total"] = "amount"
    else:
        best_amount = select_best_amount(df_cdp)
        if best_amount:
            mapping = remove_mapping_by_value(mapping, "amount")
            mapping[best_amount] = "amount"
    
    # Asegurar mapeo de Doc Nbr si existe
    for col in df_cdp.columns:
        if canonicalize(col) in ["docnbr", "nrodoc"] and "nbr_doc" not in mapping.values():
            mapping[col] = "nbr_doc"
    
    # Asegurar mapeo de invoice_number si existe
    for col in df_cdp.columns:
        if canonicalize(col) in ["invoicenumber", "numeroinvoice", "invoice_number", "numero_factura"] and "invoice_number" not in mapping.values():
            mapping[col] = "invoice_number"
    
    return mapping
