"""Validación de esquema YAML y configuración."""
from exceptions import ConfigError


# Esquema esperado de config.yaml
EXPECTED_CONFIG_SCHEMA = {
    "equivalencias_moneda": {
        "ARCA": dict,
        "genericas": dict,
    },
    "tolerancia_monto": float,
    "dashboard_colors": dict,
    "default_currency_cdp": str,
    "refresh_before_read": bool,
    "diagnostico": bool,
    "logging": {
        "level": str,
    },
    "columnas": {
        "ARCA": dict,
        "CDP": dict,
    },
}


def validate_config_schema(config):
    """
    Valida que la configuración tenga la estructura esperada.
    
    Args:
        config: Diccionario de configuración a validar
    
    Raises:
        ConfigError: Si la estructura no es válida
    """
    errors = []
    
    # Validar secciones principales
    required_keys = [
        "equivalencias_moneda",
        "tolerancia_monto",
        "dashboard_colors",
        "logging",
        "columnas",
    ]
    
    for key in required_keys:
        if key not in config:
            errors.append(f"Falta sección requerida: '{key}'")
    
    # Validar tipos específicos
    if "tolerancia_monto" in config:
        try:
            float(config["tolerancia_monto"])
        except (TypeError, ValueError):
            errors.append(f"'tolerancia_monto' debe ser numérico. Valor: {config['tolerancia_monto']}")
    
    if "logging" in config:
        if not isinstance(config["logging"], dict):
            errors.append("'logging' debe ser un objeto/diccionario")
        elif "level" in config["logging"]:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config["logging"]["level"].upper() not in valid_levels:
                errors.append(f"logging.level inválido: {config['logging']['level']}. Válidos: {valid_levels}")
    
    if "columnas" in config:
        if not isinstance(config["columnas"], dict):
            errors.append("'columnas' debe ser un objeto/diccionario")
        elif "ARCA" not in config["columnas"] or "CDP" not in config["columnas"]:
            errors.append("'columnas' debe tener 'ARCA' y 'CDP'")
    
    if "dashboard_colors" in config:
        if not isinstance(config["dashboard_colors"], dict):
            errors.append("'dashboard_colors' debe ser un diccionario")
        else:
            # Validar formato de colores hexadecimales
            for status, color in config["dashboard_colors"].items():
                if isinstance(color, str):
                    color_clean = color.lstrip('#')
                    if not _is_valid_hex_color(color_clean):
                        errors.append(f"Color inválido para '{status}': {color}")
    
    if errors:
        raise ConfigError(
            "Errores en configuración:\n" + 
            "\n".join(f"  - {e}" for e in errors)
        )


def _is_valid_hex_color(hex_string):
    """Valida que sea un color hex válido."""
    if len(hex_string) not in (3, 6):
        return False
    try:
        int(hex_string, 16)
        return True
    except ValueError:
        return False


def validate_column_mapping(config):
    """
    Valida que el mapeo de columnas sea válido.
    
    Args:
        config: Diccionario de configuración
    
    Raises:
        ConfigError: Si el mapeo no es válido
    """
    errors = []
    
    for sistema in ["ARCA", "CDP"]:
        if sistema not in config.get("columnas", {}):
            errors.append(f"Falta mapeo para sistema: {sistema}")
            continue

        mapping = config["columnas"][sistema]
        
        if not isinstance(mapping, dict):
            errors.append(f"'{sistema}' debe ser un diccionario")
            continue
        
        if not mapping:
            errors.append(f"'{sistema}' no puede estar vacío")
    
    if errors:
        raise ConfigError(
            "Errores en mapeo de columnas:\n" + 
            "\n".join(f"  - {e}" for e in errors)
        )
