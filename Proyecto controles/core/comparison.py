"""Módulo de comparación entre fuentes de datos."""
import pandas as pd
import logging


logger = logging.getLogger(__name__)


def _normalize_exchange_rate(value):
    if pd.isna(value):
        return None
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return None
        text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return text
    return value


def _is_local_currency_rate(rate):
    return isinstance(rate, (int, float)) and (0.0 == rate or (0.9 <= rate <= 1.1))


EXCHANGE_RATE_TOLERANCE = 1.0


def _exchange_rates_match(value_cdp, value_arca):
    rate_cdp = _normalize_exchange_rate(value_cdp)
    rate_arca = _normalize_exchange_rate(value_arca)
    if rate_cdp is None or rate_arca is None:
        return True
    if _is_local_currency_rate(rate_cdp) or _is_local_currency_rate(rate_arca):
        return True
    if isinstance(rate_cdp, (int, float)) and isinstance(rate_arca, (int, float)):
        rate_cdp = round(float(rate_cdp), 2)
        rate_arca = round(float(rate_arca), 2)
        return abs(rate_cdp - rate_arca) <= EXCHANGE_RATE_TOLERANCE
    return str(rate_cdp).strip() == str(rate_arca).strip()


def classify_status(row, tolerance, report_type="CDP"):
    """
    Clasifica el status de un registro según los criterios de validación.
    
    Args:
        row: Fila del DataFrame
        tolerance: Tolerancia para diferencias de monto
        report_type: Tipo de reporte ("CDP" o "E1")
    
    Returns:
        str: Estado (OK, Error de Monto, Error de Moneda, Error de Tipo Cambio, Faltante en ARCA, Duplicado en ARCA)
    """
    suffix_reporte = f"_{report_type}"
    
    # Primero verificar si falta en ARCA
    if pd.isna(row.get("amount_clean_ARCA")):
        return "Faltante en ARCA"
    
    # Verificar duplicados en ARCA
    if row.get("ARCA_dup_count", 0) >= 2:
        return "Duplicado en ARCA"
    
    # Comparar tipo de cambio si existe mapeado y con valores en ambos lados
    tipo_cambio_reporte = row.get(f"tipo_cambio{suffix_reporte}")
    tipo_cambio_arca = row.get("tipo_cambio_ARCA")
    if pd.notna(tipo_cambio_reporte) and pd.notna(tipo_cambio_arca):
        if not _exchange_rates_match(tipo_cambio_reporte, tipo_cambio_arca):
            return "Error de Tipo Cambio"
    
    # Comparar monedas
    if row.get(f"currency_norm{suffix_reporte}") != row.get("currency_norm_ARCA"):
        return "Error de Moneda"
    
    # Comparar montos
    val_reporte = row.get(f"amount_clean{suffix_reporte}", 0)
    val_arc = row.get("amount_clean_ARCA", 0)
    diff = abs(abs(val_reporte) - abs(val_arc))
    
    if diff > tolerance:
        return "Error de Monto"
    
    return "OK"


def compare_data(df_cdp_g: pd.DataFrame, df_arca_g: pd.DataFrame, 
                 tolerance: float, arca_dup_counts: pd.DataFrame,
                 cdp_keys_by_concat: dict=None, arca_count_by_key: dict=None,
                 report_type: str="CDP") -> pd.DataFrame:
    """
    Realiza la comparación entre reporte (CDP/E1) y ARCA.
    
    Args:
        df_cdp_g: DataFrame del reporte (CDP o E1)
        df_arca_g: DataFrame de ARCA
        tolerance: Tolerancia para diferencias de monto
        arca_dup_counts: Conteos de duplicados en ARCA
        cdp_keys_by_concat: Mapeo de concatenados a claves de duplicados
        arca_count_by_key: Conteo de duplicados por clave ARCA
        report_type: Tipo de reporte ("CDP" o "E1")
    
    Returns:
        DataFrame con merge y status clasificados
    """
    
    suffix_reporte = f"_{report_type}"
    
    def max_arca_count_for_concat(concat_val):
        """Obtiene el máximo contador de duplicados ARCA para un Concatenado."""
        keys = (cdp_keys_by_concat or {}).get(concat_val, [])
        if not keys:
            return 0
        return max(arca_count_by_key.get(str(k), 0) for k in keys)
    
    # Merge
    df_merge = pd.merge(
        df_cdp_g, df_arca_g,
        on="Concatenado", suffixes=(suffix_reporte, "_ARCA"), how="left"
    )
    
    df_merge["ARCA_dup_count"] = df_merge["Concatenado"].apply(max_arca_count_for_concat).astype(int)
    
    # Clasificar status
    df_merge["Status"] = df_merge.apply(lambda row: classify_status(row, tolerance, report_type), axis=1)
    
    # Calcular diferencia
    amount_col_reporte = f"amount_clean{suffix_reporte}"
    df_merge["Diferencia_Monto"] = (
        df_merge[amount_col_reporte].fillna(0) - df_merge["amount_clean_ARCA"].fillna(0)
    )
    
    return df_merge


def generate_summary(df_merge: pd.DataFrame) -> pd.DataFrame:
    """Genera resumen por estado."""
    return (
        df_merge.groupby("Status")
                .agg(Cantidad=("Concatenado", "count"))
                .reset_index()
                .sort_values("Status")
    )
