"""Tests para el agente de IA."""
import os
import pytest
from unittest.mock import patch, MagicMock
from agent import InvoiceControlAgent, DataProcessingTool, FileAnalysisTool


class TestDataProcessingTool:
    """Tests para DataProcessingTool."""

    @patch('agent.process_data')
    def test_process_data_success(self, mock_process):
        """Test procesamiento exitoso."""
        mock_process.return_value = ("output.xlsx", MagicMock(), MagicMock())

        tool = DataProcessingTool()
        result = tool._run("arca.xlsx", "cdp.xlsx")

        assert "Procesamiento completado" in result
        assert "output.xlsx" in result


class TestFileAnalysisTool:
    """Tests para FileAnalysisTool."""

    @patch('pandas.read_excel')
    @patch('pathlib.Path.exists')
    def test_analyze_file_success(self, mock_exists, mock_read):
        """Test análisis de archivo exitoso."""
        mock_exists.return_value = True
        mock_df = MagicMock()
        mock_df.columns.tolist.return_value = ['Col1', 'Col2']
        mock_df.__len__ = lambda self: 5
        mock_df.to_string.return_value = "data"
        mock_read.return_value = mock_df

        tool = FileAnalysisTool()
        result = tool._run("test.xlsx")

        assert "Columnas encontradas" in result
        assert "Col1" in result

    @patch('pathlib.Path.exists')
    def test_analyze_file_not_found(self, mock_exists):
        """Test archivo no encontrado."""
        mock_exists.return_value = False

        tool = FileAnalysisTool()
        result = tool._run("nonexistent.xlsx")

        assert "Archivo no encontrado" in result


class TestInvoiceControlAgent:
    """Tests para InvoiceControlAgent."""

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    @patch('agent.ChatOpenAI')
    @patch('agent.create_openai_tools_agent')
    @patch('agent.AgentExecutor')
    def test_agent_initialization(self, mock_executor, mock_agent, mock_llm):
        """Test inicialización del agente."""
        agent = InvoiceControlAgent()

        assert agent.api_key == 'test-key'
        assert len(agent.tools) == 4  # 4 herramientas definidas

    def test_agent_without_api_key(self):
        """Test error sin API key."""
        with pytest.raises(ValueError, match="Se requiere OPENAI_API_KEY"):
            InvoiceControlAgent()