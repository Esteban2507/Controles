"""Módulo para operaciones con Excel usando COM."""
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def read_excel_robust(file_path, sheet_name_pref):
    """Lee un archivo Excel, fallback a primera hoja si no existe la preferida."""
    import pandas as pd
    
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name_pref, engine="openpyxl")
    except ValueError:
        msg = f"Hoja '{sheet_name_pref}' no encontrada en '{Path(file_path).name}'. Leyendo primera hoja."
        logger.warning(msg)
        print(f" [AVISO] {msg}")
        return pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
