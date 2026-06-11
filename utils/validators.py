"""Módulo de validación de datos."""
import re
import unicodedata
import pandas as pd
import logging

from exceptions import ValidationError


logger = logging.getLogger(__name__)


def validate_excel_path(path):
    """Valida que el path sea un archivo Excel válido."""
    from pathlib import Path
    
    p = Path(path).resolve()
    
    if not p.exists():
        raise ValidationError(f"Archivo no existe: {p}")
    
    if p.suffix.lower() not in {'.xlsx', '.xls'}:
        raise ValidationError(f"No es archivo Excel: {p}")
    
    return p


def assert_cols(df, sistema, required_cols):
    """Verifica que un DataFrame tenga todas las columnas requeridas."""
    faltantes = [col for col in required_cols if col not in df.columns]
    
    if faltantes:
        raise ValidationError(
            f"En {sistema} faltan columnas requeridas: {faltantes}. "
            f"Disponibles: {list(df.columns)}"
        )


def canonicalize(label: str) -> str:
    """Convierte label a formato canónico para comparación."""
    if label is None:
        return ""
    
    s = str(label)
    # Normalizar Unicode (quitar acentos)
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    # Minúsculas
    s = s.lower()
    # Solo alfanuméricos
    s = re.sub(r'[^a-z0-9]+', '', s)
    
    return s


def clean_excel_errors(df):
    """Limpia valores de error de Excel en un DataFrame."""
    na_like = ["#N/A", "#¡N/A!", "#N/D", "#NOMBRE?", "#VALUE!", "#VALOR!", "#REF!", "#DIV/0!", ""]
    
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].replace(na_like, pd.NA)
    
    return df
