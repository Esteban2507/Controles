"""Sistema de logging mejorado con structured logging."""
import logging
import json
from datetime import datetime
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Formateador que produce JSON estructurado."""
    
    def format(self, record):
        """Convierte un log record a JSON."""
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'user_data'):
            log_obj["data"] = record.user_data
        
        return json.dumps(log_obj, ensure_ascii=False)


class SimpleFormatter(logging.Formatter):
    """Formateador simple para consola."""
    
    def format(self, record):
        """Formatea logs de forma legible."""
        return (
            f"[{record.levelname:8}] {record.name:20} - {record.getMessage()}"
        )


def setup_logging(config, use_structured=False):
    """
    Configura logging mejorado.
    
    Args:
        config: Diccionario de configuración
        use_structured: Si usar formato JSON (para archivos), si no, simple (consola)
    
    Returns:
        Logger configurado
    """
    level_name = config.get("logging", {}).get("level", "WARNING")
    level = getattr(logging, level_name.upper(), logging.WARNING)
    
    log_file = "control_facturas.log"
    
    # Crear logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Limpiar handlers existentes
    root_logger.handlers = []
    
    # Handler de archivo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_formatter = StructuredFormatter() if use_structured else SimpleFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = SimpleFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


def log_with_data(logger, level, message, **data):
    """
    Registra un mensaje con datos estructurados.
    
    Args:
        logger: Logger a usar
        level: Nivel (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Mensaje de log
        **data: Datos adicionales a incluir
    """
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "(unknown file)",
        0,
        message,
        (),
        None,
    )
    record.user_data = data
    logger.handle(record)
