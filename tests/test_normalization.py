"""Tests para el módulo de normalización."""
import pytest
import pandas as pd

from utils.normalization import (
    convert_amount, normalize_currency, normalize_duplicates,
    parse_date_column, remove_mapping_by_value
)


class TestConvertAmount:
    """Tests para conversión de montos."""
    
    def test_numeric_series(self, sample_amounts):
        """Test conversión de series numéricas."""
        numeric_series = pd.Series([100.5, 200.75, 150.0])
        result = convert_amount(numeric_series)
        
        assert result.dtype == 'float64' or result.dtype == 'float32'
        assert result.sum() == pytest.approx(451.25)
    
    def test_string_with_comma(self, sample_amounts):
        """Test conversión de strings con coma como decimal."""
        series = pd.Series(['100,50', '200,75'])
        result = convert_amount(series)
        
        assert result[0] == pytest.approx(100.50)
        assert result[1] == pytest.approx(200.75)
    
    def test_string_with_thousands_separator(self):
        """Test conversión de strings con separador de miles."""
        series = pd.Series(['1.500,50', '2.000,75'])
        result = convert_amount(series)
        
        assert result[0] == pytest.approx(1500.50)
        assert result[1] == pytest.approx(2000.75)
    
    def test_nan_handling(self):
        """Test que NaN se convierte a 0."""
        series = pd.Series([100.5, None, pd.NA, ''])
        result = convert_amount(series)
        
        assert result[0] == 100.5
        assert result[1] == 0
        assert result[2] == 0
        assert result[3] == 0


class TestNormalizeCurrency:
    """Tests para normalización de monedas."""
    
    def test_normalize_arca_mapping(self, sample_config):
        """Test normalización con mapeo ARCA."""
        equiv = sample_config["equivalencias_moneda"]
        
        result = normalize_currency("PES", equiv)
        assert result == "ARS"
        
        result = normalize_currency("DOL", equiv)
        assert result == "USD"
    
    def test_normalize_genericas_mapping(self, sample_config):
        """Test normalización con mapeo genérico."""
        equiv = sample_config["equivalencias_moneda"]
        
        result = normalize_currency("PESO", equiv)
        assert result == "ARS"
        
        result = normalize_currency("DOLAR", equiv)
        assert result == "USD"
    
    def test_normalize_no_mapping(self, sample_config):
        """Test que valores sin mapeo se retornan como están."""
        equiv = sample_config["equivalencias_moneda"]
        
        result = normalize_currency("XYZ", equiv)
        assert result == "XYZ"
    
    def test_normalize_none_returns_empty(self, sample_config):
        """Test que None retorna string vacío."""
        equiv = sample_config["equivalencias_moneda"]
        
        result = normalize_currency(None, equiv)
        assert result == ""
    
    def test_normalize_case_insensitive(self, sample_config):
        """Test que la normalización es case-insensitive."""
        equiv = sample_config["equivalencias_moneda"]
        
        result = normalize_currency("ars", equiv)
        assert result == "ARS"


class TestNormalizeDuplicates:
    """Tests para normalización de duplicados."""
    
    def test_strip_whitespace(self):
        """Test que se eliminan espacios."""
        series = pd.Series(['  value1  ', 'value2\t', '\nvalue3'])
        result = normalize_duplicates(series)
        
        assert result[0] == 'value1'
        assert result[1] == 'value2'
        assert result[2] == 'value3'
    
    def test_preserve_case(self):
        """Test que se preserva mayúsculas/minúsculas."""
        series = pd.Series(['Value', 'VALUE', 'value'])
        result = normalize_duplicates(series)
        
        assert result[0] == 'Value'
        assert result[1] == 'VALUE'
        assert result[2] == 'value'


class TestParseDateColumn:
    """Tests para parseo de fechas."""
    
    def test_parse_valid_dates(self):
        """Test parseo de fechas válidas."""
        df = pd.DataFrame({
            'fecha': ['2024-01-01', '2024-12-31', '2024-06-15']
        })
        
        result = parse_date_column(df, 'fecha')
        
        assert result['fecha'].dtype == 'object'  # Converted to date objects
        assert str(result['fecha'][0]) == '2024-01-01'
    
    def test_parse_column_not_exists(self):
        """Test parseo cuando columna no existe."""
        df = pd.DataFrame({'other': [1, 2, 3]})
        
        result = parse_date_column(df, 'fecha')
        
        # DataFrame sin cambios
        assert list(result.columns) == ['other']


class TestRemoveMapping:
    """Tests para remoción de mapeos."""
    
    def test_remove_single_occurrence(self):
        """Test remoción de un mapeo."""
        mapping = {'col1': 'rename_to', 'col2': 'other'}
        result = remove_mapping_by_value(mapping, 'rename_to')
        
        assert 'col1' not in result
        assert 'col2' in result
        assert result['col2'] == 'other'
    
    def test_remove_multiple_occurrences(self):
        """Test remoción de múltiples ocurrencias."""
        mapping = {
            'col1': 'amount',
            'col2': 'amount',
            'col3': 'other'
        }
        result = remove_mapping_by_value(mapping, 'amount')
        
        assert 'col1' not in result
        assert 'col2' not in result
        assert 'col3' in result
    
    def test_remove_nonexistent_value(self):
        """Test remoción de valor que no existe."""
        mapping = {'col1': 'value1', 'col2': 'value2'}
        result = remove_mapping_by_value(mapping, 'nonexistent')
        
        assert result == mapping
