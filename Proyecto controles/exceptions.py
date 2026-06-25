"""Excepciones centralizadas de la aplicación."""


class ControlError(Exception):
    """Excepción base de la aplicación."""
    pass


class ConfigError(ControlError):
    """Error en configuración."""
    pass


class ValidationError(ControlError):
    """Error en validación de datos."""
    pass


class ExcelError(ControlError):
    """Error en operaciones Excel."""
    pass


class DataProcessingError(ControlError):
    """Error en procesamiento de datos."""
    pass


class ColumnMappingError(ControlError):
    """Error en mapeo de columnas."""
    pass


class ComparisonError(ControlError):
    """Error en comparación de datos."""
    pass
