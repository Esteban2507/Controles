"""Sistema de caché para configuración."""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigCache:
    """Gestor de caché para configuración."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Inicializa el caché.
        
        Args:
            cache_dir: Directorio para almacenar caché. Si es None, usa temp.
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "control_facturas"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, file_path: Path) -> str:
        """Genera clave de caché basada en ruta y timestamp."""
        file_path = Path(file_path).resolve()
        stat = file_path.stat()
        
        # Hash de ruta + timestamp
        key_string = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Obtiene configuración del caché.
        
        Args:
            file_path: Ruta del archivo config.yaml
        
        Returns:
            Diccionario de configuración o None si no existe en caché
        """
        cache_key = self.get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        
        return None
    
    def set(self, file_path: Path, config: Dict[str, Any]) -> None:
        """
        Guarda configuración en caché.
        
        Args:
            file_path: Ruta del archivo config.yaml
            config: Diccionario de configuración a guardar
        """
        cache_key = self.get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            # Fallar silenciosamente - el caché es opcional
            import logging
            logging.debug(f"Error escribiendo caché: {e}")
    
    def clear(self) -> None:
        """Limpia todo el caché."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception:
            pass
