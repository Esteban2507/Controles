"""Tests para el módulo de validación."""
import pytest
import pandas as pd
from pathlib import Path

from utils.validators import canonicalize, clean_excel_errors, assert_cols
from exceptions import ValidationError


class TestCanonicalize:
    """Tests para canonicalización de strings."""
    
    def test_lowercase_conversion(self):
        """Test conversión a minúsculas."""
        result = canonicalize("MONTO")
        assert result == "monto"
    
    def test_remove_accents(self):
        """Test remoción de acentos."""
        result = canonicalize("NÚMERO")
        assert result == "numero"
        
        result = canonicalize("DENOMINACIÓN")
        assert result == "denominacion"
    
    def test_remove_special_chars(self):
        """Test remoción de caracteres especiales."""
        result = canonicalize("Monto Total!")
        assert result == "montototal"
        
        result = canonicalize("Importe-2")
        assert result == "importe2"
    
    def test_whitespace_handling(self):
        """Test manejo de espacios en blanco."""
        result = canonicalize("Monto Total")
        assert result == "montototal"
        
        result = canonicalize("Monto    Total")
        assert result == "montototal"
    
    def test_none_input(self):
        """Test manejo de None."""
        result = canonicalize(None)
        assert result == ""
    
    def test_numeric_preservation(self):
        """Test que números se preservan."""
        result = canonicalize("Importe2.0")
        assert "2" in result
        assert "0" in result


class TestCleanExcelErrors:
    """Tests para limpieza de errores Excel."""
    
    def test_clean_error_values(self):
        """Test limpieza de valores de error."""
        df = pd.DataFrame({
            'col1': ['#N/A', '100', '#VALUE!'],
            'col2': [200, '#DIV/0!', 300],
        })
        
        result = clean_excel_errors(df)
        
        assert pd.isna(result['col1'].iloc[0])
        assert result['col1'].iloc[1] == '100'
        assert pd.isna(result['col1'].iloc[2])
        assert result['col2'].iloc[0] == 200
    
    def test_preserve_empty_strings(self):
        """Test que strings vacíos se conviertan a NA."""
        df = pd.DataFrame({
            'col': ['', 'value', '']
        })
        
        result = clean_excel_errors(df)
        
        assert pd.isna(result['col'].iloc[0])
        assert result['col'].iloc[1] == 'value'
    
    def test_numeric_columns_unchanged(self):
        """Test que columnas numéricas se preservan."""
        df = pd.DataFrame({
            'col': [100, 200, 300]
        })
        
        original_sum = df['col'].sum()
        result = clean_excel_errors(df)
        
        assert result['col'].sum() == original_sum


class TestAssertCols:
    """Tests para validación de columnas."""
    
    def test_all_columns_present(self):
        """Test cuando todas las columnas están presentes."""
        df = pd.DataFrame({
            'col1': [1, 2],
            'col2': [3, 4],
            'col3': [5, 6],
        })
        
        # No debería lanzar excepción
        assert_cols(df, "TEST", ['col1', 'col2', 'col3'])
    
    def test_extra_columns(self):
        """Test cuando hay más columnas de las requeridas."""
        df = pd.DataFrame({
            'col1': [1, 2],
            'col2': [3, 4],
            'col3': [5, 6],
        })
        
        # Debería pasar aunque haya columnas extra
        assert_cols(df, "TEST", ['col1', 'col2'])
    
    def test_missing_single_column(self):
        """Test cuando falta una columna."""
        df = pd.DataFrame({
            'col1': [1, 2],
            'col2': [3, 4],
        })
        
        with pytest.raises(ValidationError) as exc_info:
            assert_cols(df, "TEST", ['col1', 'col2', 'col3'])
        
        assert 'col3' in str(exc_info.value)
    
    def test_missing_multiple_columns(self):
        """Test cuando faltan múltiples columnas."""
        df = pd.DataFrame({
            'col1': [1, 2],
        })
        
        with pytest.raises(ValidationError) as exc_info:
            assert_cols(df, "TEST", ['col1', 'col2', 'col3'])
        
        error_msg = str(exc_info.value)
        assert 'col2' in error_msg or 'col3' in error_msg
    
    def test_empty_dataframe(self):
        """Test con DataFrame vacío."""
        df = pd.DataFrame()
        
        with pytest.raises(ValidationError):
            assert_cols(df, "TEST", ['col1'])
