"""Tests para el módulo de configuración."""
import pytest
import tempfile
from pathlib import Path
import yaml

from utils.config import load_config, get_config_value, locate_config_file
from exceptions import ConfigError
from utils.schema_validator import validate_config_schema, validate_column_mapping


class TestConfigLoading:
    """Tests para carga de configuración."""
    
    def test_load_valid_config(self, sample_config, temp_config_file, monkeypatch):
        """Test cargando una configuración válida."""
        monkeypatch.setenv("PWD", str(temp_config_file.parent))
        monkeypatch.chdir(temp_config_file.parent)
        
        # Mock locate_config_file para retornar nuestro archivo temporal
        monkeypatch.setattr(
            "utils.config.locate_config_file",
            lambda: temp_config_file
        )
        
        config = load_config(use_cache=False)
        assert config is not None
        assert "tolerancia_monto" in config
        assert config["tolerancia_monto"] == 2.0
    
    def test_config_validation_valid(self, sample_config):
        """Test validación de schema válido."""
        # No debería lanzar excepción
        validate_config_schema(sample_config)
    
    def test_config_validation_invalid_tolerance(self, invalid_config):
        """Test que falla con tolerancia inválida."""
        with pytest.raises(ConfigError) as exc_info:
            validate_config_schema(invalid_config)
        assert "tolerancia_monto" in str(exc_info.value)
    
    def test_config_validation_invalid_logging_level(self, invalid_config):
        """Test que falla con nivel de logging inválido."""
        with pytest.raises(ConfigError) as exc_info:
            validate_config_schema(invalid_config)
        assert "logging" in str(exc_info.value).lower()
    
    def test_column_mapping_validation_valid(self, sample_config):
        """Test validación de mapeo de columnas válido."""
        # No debería lanzar excepción
        validate_column_mapping(sample_config)
    
    def test_column_mapping_validation_invalid(self, sample_config):
        """Test que falla con mapeo de columnas inválido."""
        sample_config["columnas"]["ARCA"] = None
        
        with pytest.raises(ConfigError) as exc_info:
            validate_column_mapping(sample_config)
        assert "ARCA" in str(exc_info.value)


class TestGetConfigValue:
    """Tests para obtener valores de configuración."""
    
    def test_get_simple_value(self, sample_config):
        """Test obtener valor simple."""
        result = get_config_value(sample_config, "tolerancia_monto")
        assert result == 2.0
    
    def test_get_nested_value(self, sample_config):
        """Test obtener valor anidado."""
        result = get_config_value(sample_config, "logging.level")
        assert result == "WARNING"
    
    def test_get_deep_nested_value(self, sample_config):
        """Test obtener valor profundamente anidado."""
        result = get_config_value(sample_config, "equivalencias_moneda.ARCA.PES")
        assert result == "ARS"
    
    def test_get_nonexistent_value(self, sample_config):
        """Test obtener valor inexistente retorna default."""
        result = get_config_value(sample_config, "nonexistent.key", "DEFAULT")
        assert result == "DEFAULT"
    
    def test_get_value_no_default(self, sample_config):
        """Test obtener valor inexistente sin default retorna None."""
        result = get_config_value(sample_config, "nonexistent.key")
        assert result is None
