"""Tests para el módulo de detección de columnas."""
import pytest
import pandas as pd

from core.column_detection import (
    detect_candidate_amounts, select_best_amount,
    select_best_currency
)


class TestDetectCandidateAmounts:
    """Tests para detección de columnas de monto."""
    
    def test_detect_basic_columns(self):
        """Test detección de columnas básicas de monto."""
        df = pd.DataFrame({
            'Monto': [100, 200],
            'Amount': [300, 400],
            'Fecha': ['2024-01-01', '2024-01-02']
        })
        
        result = detect_candidate_amounts(df)
        
        assert 'Monto' in result
        assert 'Amount' in result
        assert 'Fecha' not in result
    
    def test_detect_complex_names(self):
        """Test detección de nombres complejos."""
        df = pd.DataFrame({
            'Monto Total': [100],
            'Importe Total': [200],
            'Importe 2': [300],
        })
        
        result = detect_candidate_amounts(df)
        
        assert 'Monto Total' in result or 'Importe Total' in result
    
    def test_no_candidates(self):
        """Test cuando no hay columnas de monto."""
        df = pd.DataFrame({
            'Fecha': ['2024-01-01'],
            'Proveedor': ['Vendor A'],
        })
        
        result = detect_candidate_amounts(df)
        
        assert len(result) == 0


class TestSelectBestAmount:
    """Tests para selección de mejor columna de monto."""
    
    def test_select_by_most_values(self):
        """Test selección por cantidad de valores no-nulos."""
        df = pd.DataFrame({
            'Monto': [100, 200, 300, None],
            'Monto Total': [None, 400, None, None],
        })
        
        result = select_best_amount(df)
        
        assert result == 'Monto'  # Tiene 3 valores válidos
    
    def test_select_single_option(self):
        """Test cuando hay una sola opción."""
        df = pd.DataFrame({
            'Monto': [100, 200],
            'Fecha': ['2024-01-01', '2024-01-02'],
        })
        
        result = select_best_amount(df)
        
        assert result == 'Monto'
    
    def test_select_no_candidates(self):
        """Test cuando no hay candidatos."""
        df = pd.DataFrame({
            'Fecha': ['2024-01-01'],
            'Proveedor': ['Vendor'],
        })
        
        result = select_best_amount(df)
        
        assert result is None


class TestSelectBestCurrency:
    """Tests para selección de mejor columna de moneda."""
    
    def test_select_preferred_name(self):
        """Test selección por nombre preferido."""
        df = pd.DataFrame({
            'Moneda': ['ARS', 'USD'],
            'currency': ['EUR', 'GBP'],
        })
        
        result = select_best_currency(df)
        
        assert result == 'Moneda'  # Nombre preferido
    
    def test_select_first_valid(self):
        """Test selección del primero con valores."""
        df = pd.DataFrame({
            'Moneda': ['', ''],  # Vacío
            'Moneda 2': ['ARS', 'USD'],  # Tiene valores
        })
        
        result = select_best_currency(df)
        
        assert result is not None
    
    def test_select_no_candidates(self):
        """Test cuando no hay candidatos."""
        df = pd.DataFrame({
            'Monto': [100, 200],
            'Fecha': ['2024-01-01', '2024-01-02'],
        })
        
        result = select_best_currency(df)
        
        assert result is None
    
    def test_select_any_candidate(self):
        """Test selección de cualquier candidato si no hay preferencias."""
        df = pd.DataFrame({
            'currency': ['ARS', 'USD'],
            'Moneda_Alt': ['EUR', 'GBP'],
        })
        
        result = select_best_currency(df)
        
        assert result in ['currency', 'Moneda_Alt']
