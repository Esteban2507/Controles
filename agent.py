"""Agente de IA para procesamiento de control de facturas con soporte para OpenAI y Azure OpenAI (GitHub Copilot)."""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
import pandas as pd

from core.process import process_data
from utils.config import load_config
from utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)


class DataProcessingTool(BaseTool):
    """Herramienta para procesar datos de facturas."""
    name: str = "process_invoice_data"
    description: str = "Procesa archivos de ARCA, CDP y/o E1 para generar reporte de control de facturas. E1 es opcional; al menos ARCA y uno de CDP/E1 deben ingresarse."

    def _run(self, arca_path: str, cdp_path: str, e1_path: str = "", fecha_filtro: str = None) -> str:
        """Ejecuta el procesamiento de datos."""
        try:
            config = load_config()
            fecha = None
            if fecha_filtro and fecha_filtro != "Todas las fechas":
                from datetime import datetime
                fecha = datetime.strptime(fecha_filtro, "%Y-%m-%d").date()

            output_path, df_resumen, df_err = process_data(config, arca_path, cdp_path, e1_path, fecha)

            summary = f"Procesamiento completado. Reporte generado en: {output_path}\n"
            summary += f"Resumen:\n{df_resumen.to_string(index=False)}\n"
            if not df_err.empty:
                summary += f"\nErrores encontrados: {len(df_err)} registros\n"
                summary += f"Primeros errores:\n{df_err.head().to_string(index=False)}"

            return summary
        except Exception as e:
            logger.error(f"Error en procesamiento: {e}", exc_info=True)
            return f"Error durante el procesamiento: {str(e)}"


class AskUserTool(BaseTool):
    """Herramienta para hacer preguntas al usuario."""
    name: str = "ask_user"
    description: str = "Pregunta al usuario por información adicional cuando sea necesaria."

    def _run(self, question: str) -> str:
        """Hace una pregunta al usuario."""
        response = input(f"🤖 Necesito más información: {question}\n👤 Tú: ")
        return response


class FileAnalysisTool(BaseTool):
    """Herramienta para analizar archivos antes del procesamiento."""
    name: str = "analyze_file"
    description: str = "Analiza un archivo Excel para entender su estructura y columnas."

    def _run(self, file_path: str) -> str:
        """Analiza el archivo."""
        try:
            if not Path(file_path).exists():
                return f"Archivo no encontrado: {file_path}"

            df = pd.read_excel(file_path, nrows=5)  # Solo primeras filas
            cols = []
            try:
                cols = df.columns.tolist()
            except Exception:
                try:
                    cols = list(df.columns)
                except Exception:
                    cols = []

            analysis = f"Análisis del archivo {Path(file_path).name}:\n"
            analysis += f"Columnas encontradas: {cols}\n"
            analysis += f"Número de filas (muestra): {len(df)}\n"
            analysis += f"Primeras filas:\n{df.to_string(index=False)}"

            return analysis
        except Exception as e:
            return f"Error analizando archivo: {str(e)}"


class ErrorAnalysisTool(BaseTool):
    """Herramienta para analizar errores en detalle."""
    name: str = "analyze_errors"
    description: str = "Analiza los errores encontrados en el procesamiento y sugiere soluciones."

    def _run(self, error_summary: str) -> str:
        """Analiza errores."""
        # Aquí podría usar IA para categorizar errores y sugerir fixes
        return f"Análisis de errores: {error_summary}\nSugerencias: Revisar mapeos de columnas, verificar formatos de fecha, ajustar tolerancias."


class InvoiceControlAgent:
    """Agente de IA para control de facturas con soporte para OpenAI y Azure OpenAI."""

    def __init__(self, api_key: str = None, use_azure: bool = False, azure_config: dict = None):
        """
        Inicializa el agente.

        Args:
            api_key: API key (OpenAI o Azure)
            use_azure: Si usar Azure OpenAI
            azure_config: Configuración para Azure (endpoint, deployment_name, api_version)
        """
        self.use_azure = use_azure
        self.api_key = api_key
        # Permitir tomar API key desde variable de entorno cuando no se pasa como argumento
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        self.azure_config = azure_config or {}

        if not self.api_key:
            raise ValueError("Se requiere OPENAI_API_KEY")

        # Configurar el LLM según el proveedor
        if self.use_azure:
            self.llm = AzureChatOpenAI(
                azure_endpoint=self.azure_config.get("endpoint"),
                azure_deployment=self.azure_config.get("deployment_name", "gpt-4"),
                api_version=self.azure_config.get("api_version", "2024-02-01"),
                api_key=self.api_key,
                temperature=0.1,
            )
        else:
            self.llm = ChatOpenAI(
                model="gpt-4-turbo-preview",
                temperature=0.1,
                api_key=self.api_key
            )

        self.tools = [
            DataProcessingTool(),
            AskUserTool(),
            FileAnalysisTool(),
            ErrorAnalysisTool(),
        ]

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un agente especializado en control y reconciliación de facturas entre sistemas ARCA, CDP y E1.

Tu objetivo es ayudar al usuario a procesar datos de facturas, identificar discrepancias y generar reportes de manera interactiva.

Funciones disponibles:
- Procesar archivos de datos y generar reportes de control
- Analizar archivos para entender su estructura
- Hacer preguntas al usuario cuando necesites más información
- Analizar errores y proporcionar insights accionables
- Iterar en procesos cuando sea necesario

Comportamiento:
- Sé proactivo: si no tienes toda la información, pregunta
- Explica cada paso que das
- Si hay errores, analiza y sugiere soluciones
- Mantén un diálogo natural y útil
- Cuando completes una tarea, pregunta si quieres hacer algo más

Ejemplos de interacciones:
- Usuario: "Procesa estos archivos" → Pregunta por las rutas si no las tienes
- Usuario: "Hay errores" → Analiza los errores y sugiere correcciones
- Usuario: "Analiza este archivo" → Examina columnas y estructura"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15
        )

    def run(self, user_input: str) -> str:
        """Ejecuta el agente con la entrada del usuario."""
        try:
            result = self.executor.invoke({"input": user_input})
            return result["output"]
        except Exception as e:
            logger.error(f"Error en ejecución del agente: {e}", exc_info=True)
            return f"Error: {str(e)}"

    def interactive_session(self):
        """Inicia una sesión interactiva."""
        provider_name = "Azure OpenAI (GitHub Copilot)" if self.use_azure else "OpenAI"
        print(f"🤖 Agente de Control de Facturas - Sesión Interactiva ({provider_name})")
        print("Escribe 'salir' para terminar.")
        print("-" * 50)

        while True:
            user_input = input("\n👤 Tú: ")
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("¡Hasta luego!")
                break

            response = self.run(user_input)
            print(f"\n🤖 Agente: {response}")


def create_agent_from_config():
    """Crea un agente basado en la configuración del config.yaml."""
    config = load_config()

    # Intentar Azure OpenAI primero (GitHub Copilot)
    azure_config = config.get("azure_openai", {})
    if azure_config.get("api_key") and azure_config.get("endpoint"):
        print("🔗 Usando Azure OpenAI (compatible con GitHub Copilot)")
        return InvoiceControlAgent(
            api_key=azure_config["api_key"],
            use_azure=True,
            azure_config=azure_config
        )

    # Fallback a OpenAI directo
    api_key = os.getenv("OPENAI_API_KEY") or config.get("openai_api_key")
    if api_key:
        print("🔗 Usando OpenAI directo")
        return InvoiceControlAgent(api_key=api_key, use_azure=False)

    raise ValueError("No se encontró configuración válida para OpenAI o Azure OpenAI")


def main():
    """Función principal para ejecutar el agente."""
    try:
        config = load_config()
        setup_logging(config)

        agent = create_agent_from_config()
        agent.interactive_session()

    except Exception as e:
        logger.error(f"Error iniciando agente: {e}", exc_info=True)
        print(f"Error: {e}")


if __name__ == "__main__":
    main()