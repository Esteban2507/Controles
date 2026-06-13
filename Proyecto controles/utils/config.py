"""Módulo de gestión de configuración."""
import sys
import logging
from pathlib import Path
import yaml

from exceptions import ConfigError
from utils.schema_validator import validate_config_schema, validate_column_mapping
from utils.cache import ConfigCache
from utils.logging_setup import setup_logging as _setup_logging


logger = logging.getLogger(__name__)
_config_cache = ConfigCache()


def locate_config_file():
    """Localiza el archivo config.yaml en múltiples ubicaciones."""
    search_paths = []
    
    # Si está empaquetado con PyInstaller
    if hasattr(sys, '_MEIPASS'):
        search_paths.append(Path(sys.executable).parent / "config.yaml")
    
    # En el directorio del script
    search_paths.append(Path(__file__).resolve().parent.parent / "config.yaml")
    
    # En el CWD
    search_paths.append(Path.cwd() / "config.yaml")
    
    for path in search_paths:
        if path.exists():
            return path
    
    raise ConfigError(
        f"No se encontró 'config.yaml' en:\n" + 
        "\n".join(f"  - {p}" for p in search_paths)
    )


def load_config(use_cache=True):
    """
    Carga y valida la configuración desde YAML.
    
    Args:
        use_cache: Si usar caché para config previamente cargadas
    
    Returns:
        Diccionario de configuración validado
    
    Raises:
        ConfigError: Si hay errores en la configuración
    """
    cfg_path = locate_config_file()
    
    # Intentar obtener del caché
    if use_cache:
        cached_config = _config_cache.get(cfg_path)
        if cached_config is not None:
            logger.debug(f"Configuración cargada desde caché: {cfg_path}")
            return cached_config
    
    # Cargar del archivo
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ConfigError(f"El archivo {cfg_path} está vacío.")
        
        # Validar schema
        validate_config_schema(config)
        validate_column_mapping(config)
        
        # Guardar en caché
        if use_cache:
            _config_cache.set(cfg_path, config)
        
        logger.debug(f"Configuración cargada y validada: {cfg_path}")
        return config
        
    except yaml.YAMLError as e:
        raise ConfigError(f"Error al parsear YAML en {cfg_path}: {e}")
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Error al cargar configuración: {e}")


def get_config_value(config, key_path, default=None):
    """
    Obtiene valor de config usando path tipo 'logging.level'.
    
    Args:
        config: Diccionario de configuración
        key_path: Path separado por puntos (ej: 'logging.level')
        default: Valor por defecto si no existe
    
    Returns:
        Valor encontrado o default
    """
    keys = key_path.split(".")
    value = config
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default
    
    return value


def setup_logging(config, use_structured=False):
    """
    Configura logging basado en el archivo de configuración.
    
    Args:
        config: Diccionario de configuración
        use_structured: Si usar formato JSON estructurado
    
    Returns:
        Logger configurado
    """
    return _setup_logging(config, use_structured=use_structured)
