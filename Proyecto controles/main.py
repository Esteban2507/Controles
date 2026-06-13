"""Punto de entrada de la aplicación de Control de Facturas."""
import sys
import tkinter as tk
import logging

from utils.config import load_config, setup_logging, ConfigError
from ui.gui import ControlApp


def main():
    """Función principal."""
    try:
        # Cargar configuración
        config = load_config()
        
        # Configurar logging
        setup_logging(config)
        
        # Crear ventana principal
        root = tk.Tk()
        app = ControlApp(root, config)
        root.mainloop()
        
    except ConfigError as e:
        print(f"[ERROR CONFIGURACIÓN] {e}")
        input("Presiona Enter para salir...")
        sys.exit(1)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Presiona Enter para salir...")
        sys.exit(1)


if __name__ == "__main__":
    main()