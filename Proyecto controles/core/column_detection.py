"""Módulo de detección automática de columnas."""
import pandas as pd
import logging
from utils.validators import canonicalize


logger = logging.getLogger(__name__)


def detect_candidate_amounts(df: pd.DataFrame):
    """Detecta columnas candidatas para monto."""
    candidates = []
    for col in df.columns:
        c = canonicalize(col)
        if c in ("monto", "montototal", "imptotal", "imptotal2", "amount"):
            candidates.append(col)
    
    # Eliminar duplicados manteniendo orden
    seen, result = set(), []
    for c in candidates:
        if c not in seen:
            result.append(c)
            seen.add(c)
    
    return result


def select_best_amount(df: pd.DataFrame) -> str | None:
    """Selecciona la mejor columna de monto por cantidad de valores válidos."""
    from utils.normalization import convert_amount
    
    candidates = detect_candidate_amounts(df)
    
    if not candidates:
        return None
    
    best, best_score = None, -1
    
    for col in candidates:
        values = convert_amount(df[col])
        score = values.notna().sum()
        
        if score > best_score:
            best, best_score = col, score
    
    if len(candidates) > 1 and best is not None:
        logger.info(f"Varias columnas de monto {candidates}. Usando '{best}'.")
    
    return best


def select_best_currency(df: pd.DataFrame) -> str | None:
    """Selecciona la mejor columna de moneda."""
    candidates = [c for c in df.columns if canonicalize(c) in ("moneda", "moneda2", "currency")]
    
    if not candidates:
        return None
    
    # Preferencia de nombres
    for pref in ["Moneda", "currency", "Moneda 2"]:
        if pref in df.columns:
            s = df[pref].astype(str).str.strip()
            if s.notna().any() and (s != "").any():
                return pref
    
    return candidates[0]
