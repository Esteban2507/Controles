"""Módulo para operaciones con Excel usando COM."""
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def read_excel_robust(file_path, sheet_name_pref):
    """Lee un archivo Excel, fallback a primera hoja si no existe la preferida."""
    import pandas as pd
    
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name_pref, engine="openpyxl")
    except ValueError:
        msg = f"Hoja '{sheet_name_pref}' no encontrada en '{Path(file_path).name}'. Leyendo primera hoja."
        logger.warning(msg)
        print(f" [AVISO] {msg}")
        return pd.read_excel(file_path, sheet_name=0, engine="openpyxl")


def refresh_excel_workbooks(file_paths, progress_callback=None):
    """
    Refresca conexiones y tablas dinámicas de una lista de archivos Excel usando COM.
    
    Args:
        file_paths: Lista de paths de archivos Excel a refrescar.
        progress_callback: Función callable(str) para reportar progreso.
    """
    import pythoncom
    import win32com.client
    
    if not file_paths:
        return
        
    pythoncom.CoInitialize()
    excel = None
    try:
        if progress_callback:
            progress_callback("Iniciando instancia de Excel...")
        
        # Iniciar Excel de manera independiente
        excel = win32com.client.DispatchEx("Excel.Application")
        
        # Configurar propiedades de seguridad
        try:
            excel.Visible = False
        except Exception as e:
            logger.warning(f"No se pudo establecer excel.Visible = False: {e}")
        try:
            excel.DisplayAlerts = False
        except Exception as e:
            logger.warning(f"No se pudo establecer excel.DisplayAlerts = False: {e}")
        try:
            excel.AskToUpdateLinks = False
        except Exception as e:
            logger.warning(f"No se pudo establecer excel.AskToUpdateLinks = False: {e}")
        try:
            excel.ScreenUpdating = False
        except Exception as e:
            logger.warning(f"No se pudo establecer excel.ScreenUpdating = False: {e}")

        for path in file_paths:
            if not path:
                continue
            path_obj = Path(path)
            if not path_obj.exists():
                msg = f"El archivo no existe: {path}"
                logger.error(msg)
                if progress_callback:
                    progress_callback(f"[ERROR] {msg}")
                raise FileNotFoundError(msg)
                
            file_name = path_obj.name
            abs_path = str(path_obj.resolve())
            
            if progress_callback:
                progress_callback(f"Abriendo {file_name}...")
            
            # Abrir el libro de trabajo con UpdateLinks=3 (actualiza todas las referencias externas)
            wb = excel.Workbooks.Open(abs_path, UpdateLinks=3, ReadOnly=False)
            
            try:
                if progress_callback:
                    progress_callback(f"Configurando conexiones de {file_name}...")
                
                # Deshabilitar background refresh para que la actualización sea síncrona
                for conn in wb.Connections:
                    try:
                        if conn.Type == 1:  # OLEDB
                            conn.OLEDBConnection.BackgroundQuery = False
                        elif conn.Type == 2:  # ODBC
                            conn.ODBCConnection.BackgroundQuery = False
                    except Exception as e:
                        logger.warning(f"No se pudo deshabilitar BackgroundQuery en {file_name}: {e}")
                
                if progress_callback:
                    progress_callback(f"Refrescando consultas de {file_name}...")
                
                # Refrescar todo el libro
                wb.RefreshAll()
                
                # Esperar a que terminen las consultas asíncronas
                try:
                    excel.CalculateUntilAsyncQueriesDone()
                except Exception:
                    pass
                
                if progress_callback:
                    progress_callback(f"Actualizando tablas dinámicas de {file_name}...")
                
                # Refrescar todas las tablas dinámicas
                for sheet in wb.Sheets:
                    for pivot in sheet.PivotTables():
                        try:
                            pivot.RefreshTable()
                        except Exception as e:
                            logger.warning(f"No se pudo refrescar PivotTable en sheet {sheet.Name}: {e}")
                
                if progress_callback:
                    progress_callback(f"Guardando {file_name}...")
                
                # Recalcular todo el libro antes de guardar
                excel.Calculate()
                wb.Save()
                wb.Close(SaveChanges=True)
                wb = None
                
            except Exception as e:
                logger.error(f"Fallo durante el procesamiento de {file_name}: {e}", exc_info=True)
                if progress_callback:
                    progress_callback(f"[ERROR] {file_name}: {e}")
                raise e
            finally:
                if wb is not None:
                    try:
                        wb.Close(SaveChanges=False)
                    except Exception:
                        pass
                    
        if progress_callback:
            progress_callback("Todos los archivos fueron actualizados exitosamente.")
            
    except Exception as e:
        logger.error(f"Error general en refresco Excel COM: {e}", exc_info=True)
        raise e
    finally:
        if excel is not None:
            try:
                excel.Quit()
            except Exception as e:
                logger.warning(f"No se pudo cerrar la aplicación Excel: {e}")
        pythoncom.CoUninitialize()

