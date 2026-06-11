"""Selector de modo para la aplicación de Control de Facturas."""
import sys
import os
from pathlib import Path

def show_menu():
    """Muestra el menú de selección de modo."""
    print("🚀 Control de Facturas - Selector de Modo")
    print("=" * 50)
    print("1. 🖥️  Interfaz Gráfica (GUI)")
    print("2. 🤖 Agente de IA Interactivo (OpenAI/Azure)")
    print("3. ❌ Salir")
    print()

def main():
    """Función principal del launcher."""
    while True:
        show_menu()
        choice = input("Selecciona una opción (1-3): ").strip()

        if choice == "1":
            print("Iniciando Interfaz Gráfica...")
            # Importar aquí para evitar cargar tkinter si no se usa
            try:
                from main import main as gui_main
                gui_main()
            except ImportError as e:
                print(f"Error cargando GUI: {e}")
                print("Asegúrate de tener instaladas las dependencias necesarias.")
            break

        elif choice == "2":
            print("Iniciando Agente de IA...")
            try:
                from agent import main as agent_main
                agent_main()
            except ImportError as e:
                print(f"Error cargando agente IA: {e}")
                print("Asegúrate de tener instaladas las dependencias de IA:")
                print("pip install langchain openai langchain-openai")
            except Exception as e:
                print(f"Error en agente IA: {e}")
            break

        elif choice == "3":
            print("¡Hasta luego!")
            sys.exit(0)

        else:
            print("Opción inválida. Intenta de nuevo.\n")

if __name__ == "__main__":
    main()