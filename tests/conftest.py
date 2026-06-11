"""Configuración compartida para tests."""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import yaml
import sys

# Agregar directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_dataframe():
    """Fixture que proporciona un DataFrame de ejemplo."""
    return pd.DataFrame({
        'Fecha': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Monto': [100.50, 200.75, 150.25],
        'Moneda': ['ARS', 'USD', 'EUR'],
        'Proveedor': ['Vendor A', 'Vendor B', 'Vendor C'],
        'Concatenado': ['CONCAT1', 'CONCAT2', 'CONCAT3'],
        'duplicados': ['KEY1', 'KEY2', 'KEY1'],
    })


@pytest.fixture
def empty_dataframe():
    """Fixture que proporciona un DataFrame vacío."""
    return pd.DataFrame({
        'Fecha': [],
        'Monto': [],
        'Moneda': [],
        'Proveedor': [],
        'Concatenado': [],
        'duplicados': [],
    })


@pytest.fixture
def sample_config():
    """Fixture que proporciona una configuración de ejemplo."""
    return {
        "equivalencias_moneda": {
            "ARCA": {
                "PES": "ARS",
                "DOL": "USD",
                "EUR": "EUR",
            },
            "genericas": {
                "PESO": "ARS",
                "DOLAR": "USD",
                "EURO": "EUR",
            }
        },
        "tolerancia_monto": 2.0,
        "dashboard_colors": {
            "OK": "00B050",
            "Error de Monto": "FF99CC",
            "Error de Moneda": "FFFF00",
            "Error de Tipo Cambio": "FFB347",
        },
        "default_currency_cdp": "EUR",
        "refresh_before_read": False,
        "diagnostico": False,
        "logging": {
            "level": "WARNING"
        },
        "columnas": {
            "ARCA": {
                "Fecha": "issue_date",
                "Monto": "amount",
                "Moneda": "currency",
                "Proveedor": "vendor",
                "Tipo Cambio": "tipo_cambio",
            },
            "CDP": {
                "Fecha": "issue_date",
                "Monto": "amount",
                "Moneda": "currency",
                "Proveedor": "vendor",
                "Tipo Cambio": "tipo_cambio",
            }
        }
    }


@pytest.fixture
def temp_config_file(sample_config, tmp_path):
    """Fixture que crea un archivo config.yaml temporal."""
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f)
    return config_file


@pytest.fixture
def invalid_config():
    """Fixture que proporciona una configuración inválida."""
    return {
        "tolerancia_monto": "NO_ES_NUMERO",  # Debería ser float
        "logging": {
            "level": "INVALID_LEVEL"  # Nivel inválido
        },
        # Faltan secciones requeridas
    }


@pytest.fixture
def sample_amounts():
    """Fixture que proporciona una serie de montos."""
    return pd.Series([
        100.50,
        "200,75",  # String con coma
        "1.500,50",  # String con separador de miles
        None,
        "",
    ])


@pytest.fixture
def sample_currencies():
    """Fixture que proporciona una serie de monedas."""
    return pd.Series([
        "ARS",
        "PES",  # Equivalente a ARS
        "USD",
        "DOL",  # Equivalente a USD
        None,
    ])


@pytest.fixture(autouse=True)
def cleanup_imports():
    """Limpia imports entre tests para evitar efectos laterales."""
    yield
    # Limpieza después de cada test
    if 'utils.cache' in sys.modules:
        # Limpiar caché entre tests
        try:
            from utils.cache import ConfigCache
            cache = ConfigCache()
            cache.clear()
        except Exception:
            pass
