"""Módulo de normalización de datos."""
import pandas as pd
import logging


logger = logging.getLogger(__name__)


def convert_amount(series: pd.Series) -> pd.Series:
    """Convierte una serie a valores numéricos de monto."""
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0).astype(float)

    def _parse_value(x):
        if pd.isna(x) or x == "":
            return 0.0
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip()
        if s == "":
            return 0.0
        # Si contiene ambos separadores, asumimos formato europeo: '.' miles, ',' decimales
        if "." in s and "," in s:
            s = s.replace('.', '').replace(',', '.')
        # Si solo contiene coma, asumir coma decimal
        elif "," in s and "." not in s:
            s = s.replace(',', '.')
        # Si solo contiene punto, asumir punto decimal (no tocar)
        try:
            return float(s)
        except Exception:
            return 0.0

    return series.apply(_parse_value).astype(float)


def normalize_currency(value, equivalencies):
    """Normaliza un código de moneda usando mapeo de equivalencias."""
    if pd.isna(value) or value is None:
        return ""
    
    v = str(value).strip().upper()
    
    # Buscar en ARCA
    if v in equivalencies.get("ARCA", {}):
        return equivalencies["ARCA"][v]
    
    # Buscar en genéricas
    if v in equivalencies.get("genericas", {}):
        return equivalencies["genericas"][v]
    
    return v


def normalize_duplicates(series: pd.Series) -> pd.Series:
    """Normaliza valores de duplicados (espacios)."""
    return series.astype(str).str.strip()


def parse_date_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Convierte una columna a tipo fecha."""
    if col not in df.columns:
        return df
    
    df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    return df


def remove_mapping_by_value(mapping, value):
    """Remueve todas las claves de un mapping que tienen valor específico."""
    result = {}
    for k, v in mapping.items():
        if v == value:
            continue
        if isinstance(v, list) and value in v:
            continue
        result[k] = v
    return result
