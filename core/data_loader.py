"""Módulo de carga y preparación de datos."""
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from utils.excel import read_excel_robust
from utils.validators import clean_excel_errors
from utils.normalization import (
    convert_amount, normalize_currency, normalize_duplicates, parse_date_column
)


logger = logging.getLogger(__name__)


class DataLoader:
    """Gestor de carga de datos desde archivos Excel."""
    
    def __init__(self, config):
        self.config = config
        self.equiv = config.get("equivalencias_moneda", {})
        self.diagnostico = bool(config.get("diagnostico", False))
    
    def load_arca(self, arca_path):
        """Carga y prepara datos ARCA."""
        logger.info("Cargando ARCA...")
        print("1/8 Leyendo ARCA (hoja 'AFIP' o primera)...")
        
        df = read_excel_robust(arca_path, "AFIP")
        print(f"   ARCA filas={len(df):,} cols={len(df.columns)}")
        
        if self.diagnostico:
            print("   Encabezados ARCA (crudos):", list(df.columns)[:30])
        
        return df
    
    def load_cdp(self, cdp_path, fecha_filtro=None):
        """Carga y prepara datos CDP, opcional con filtro de fecha."""
        if not cdp_path:
            logger.info("CDP no provisto, inicializando vacío...")
            print("2/8 Leyendo CDP (hoja 'CDP' o primera)...")
            print("   CDP no provisto, inicializando vacío...")
            return pd.DataFrame()
        
        logger.info("Cargando CDP...")
        print("2/8 Leyendo CDP (hoja 'CDP' o primera)...")

        df = None
        try:
            df = read_excel_robust(cdp_path, "CDP")
        except Exception:
            df = read_excel_robust(cdp_path, 0)
        print(f"   CDP filas={len(df):,} cols={len(df.columns)}")
        
        if self.diagnostico:
            print("   Encabezados CDP (crudos):", list(df.columns)[:30])
        
        # Detectar columna de posting y crear posting_date_CDP
        col_fecha_posting = self._find_posting_date_column(df)
        if col_fecha_posting:
            df["posting_date_CDP"] = pd.to_datetime(df[col_fecha_posting], errors='coerce').dt.date
        else:
            df["posting_date_CDP"] = pd.NaT
 
        # Aplicar filtro de fecha si se especificó
        if fecha_filtro is not None:
            if col_fecha_posting:
                print(f"   Aplicando filtro de fecha desde {fecha_filtro} en '{col_fecha_posting}'")
                df[col_fecha_posting] = pd.to_datetime(df[col_fecha_posting], errors='coerce')
                df = df[df[col_fecha_posting].dt.date >= fecha_filtro].copy()
                print(f"   Filas después del filtro: {len(df):,}")
            else:
                logger.warning("No se encontró columna de posting date para filtro")
                print(f"   [AVISO] No se encontró columna de posting date")
        
        return df
    
    def load_e1(self, e1_path, fecha_filtro=None):
        """Carga y prepara datos E1, opcional con filtro de fecha."""
        if not e1_path:
            logger.info("E1 no provisto, inicializando vacío...")
            return pd.DataFrame()
        
        logger.info("Cargando E1...")
        print("2b/8 Leyendo E1 (hoja 'E1' o primera)...")

        df = None
        try:
            df = read_excel_robust(e1_path, "E1")
        except Exception:
            df = read_excel_robust(e1_path, 0)
        print(f"   E1 filas={len(df):,} cols={len(df.columns)}")
        
        if self.diagnostico:
            print("   Encabezados E1 (crudos):", list(df.columns)[:30])
        
        # Detectar columna de posting y crear posting_date_E1
        col_fecha_posting = self._find_posting_date_column(df)
        if col_fecha_posting:
            df["posting_date_E1"] = pd.to_datetime(df[col_fecha_posting], errors='coerce').dt.date
        else:
            df["posting_date_E1"] = pd.NaT
 
        # Aplicar filtro de fecha si se especificó
        if fecha_filtro is not None:
            if col_fecha_posting:
                print(f"   Aplicando filtro de fecha desde {fecha_filtro} en '{col_fecha_posting}'")
                df[col_fecha_posting] = pd.to_datetime(df[col_fecha_posting], errors='coerce')
                df = df[df[col_fecha_posting].dt.date >= fecha_filtro].copy()
                print(f"   Filas después del filtro: {len(df):,}")
            else:
                logger.warning("No se encontró columna de posting date para filtro E1")
                print(f"   [AVISO] No se encontró columna de posting date")
        
        return df
    
    @staticmethod
    def _find_posting_date_column(df):
        """Busca una columna de posting date en un DataFrame."""
        for col in df.columns:
            col_lower = str(col).lower()
            if "posting" in col_lower and ("fecha" in col_lower or "date" in col_lower or "posting" in col_lower):
                return col
        return None
    
    def prepare_arca(self, df_arca_raw):
        """Prepara y normaliza datos ARCA."""
        print("5/8 Normalizando montos/monedas/fechas ...")
        
        # Limpiar errores Excel
        df_arca_raw = clean_excel_errors(df_arca_raw)
        
        # Parsear fechas
        df_arca_raw = parse_date_column(df_arca_raw, "issue_date")
        
        # Normalizar montos
        df_arca_raw["amount_clean"] = convert_amount(df_arca_raw["amount"])
        
        # Normalizar monedas
        df_arca_raw["currency_norm"] = df_arca_raw["currency"].apply(
            lambda x: normalize_currency(x, self.equiv)
        )
        
        # Normalizar duplicados
        df_arca_raw["duplicados"] = normalize_duplicates(df_arca_raw["duplicados"])
        
        return df_arca_raw
    
    def prepare_cdp(self, df_cdp):
        """Prepara y normaliza datos CDP."""
        if df_cdp.empty:
            return df_cdp
        
        # Limpiar errores Excel
        df_cdp = clean_excel_errors(df_cdp)
        
        # Eliminar filas sin concatenado
        df_cdp = df_cdp[~df_cdp["Concatenado"].isna()].copy()
        
        # Agregar columnas si faltan
        if "erp" not in df_cdp.columns:
            df_cdp["erp"] = "(sin ERP)"
        if "doc_type" not in df_cdp.columns:
            df_cdp["doc_type"] = ""
        
        # Parsear fechas
        df_cdp = parse_date_column(df_cdp, "issue_date")
        
        # Normalizar montos
        df_cdp["amount_clean"] = convert_amount(df_cdp["amount"])
        
        # Normalizar monedas
        df_cdp["currency_norm"] = df_cdp["currency"].apply(
            lambda x: normalize_currency(x, self.equiv)
        )
        
        # Normalizar duplicados
        df_cdp["duplicados"] = normalize_duplicates(df_cdp["duplicados"])
        
        # Moneda por defecto si está vacía
        default_curr = self.config.get("default_currency_cdp", None)
        if default_curr and "currency" in df_cdp.columns:
            df_cdp["currency"] = df_cdp["currency"].fillna(default_curr).replace("", default_curr)
        
        return df_cdp

    def prepare_e1(self, df_e1):
        """Prepara y normaliza datos E1."""
        if df_e1.empty:
            return df_e1
        
        # Limpiar errores Excel
        df_e1 = clean_excel_errors(df_e1)
        
        # Eliminar filas sin concatenado
        df_e1 = df_e1[~df_e1["Concatenado"].isna()].copy()
        
        # Agregar columnas si faltan
        if "erp" not in df_e1.columns:
            df_e1["erp"] = "(sin ERP)"
        if "doc_type" not in df_e1.columns:
            df_e1["doc_type"] = ""
        
        # Parsear fechas
        df_e1 = parse_date_column(df_e1, "issue_date")
        
        # Normalizar montos
        df_e1["amount_clean"] = convert_amount(df_e1["amount"])
        
        # Normalizar monedas
        df_e1["currency_norm"] = df_e1["currency"].apply(
            lambda x: normalize_currency(x, self.equiv)
        )
        
        # Normalizar duplicados
        df_e1["duplicados"] = normalize_duplicates(df_e1["duplicados"])
        
        # Moneda por defecto si está vacía
        default_curr = self.config.get("default_currency_e1", None)
        if default_curr and "currency" in df_e1.columns:
            df_e1["currency"] = df_e1["currency"].fillna(default_curr).replace("", default_curr)
        
        return df_e1
