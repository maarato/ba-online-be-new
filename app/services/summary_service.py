from typing import Optional, Dict, List, Any
import json
from datetime import datetime
from .mysql_service import mysql_service

class SummaryService:
    
    def create_summary(self, device_id: str, summary_data: Dict) -> Optional[int]:
        """
        Crea un nuevo resumen en la base de datos
        
        Args:
            device_id: ID del dispositivo
            summary_data: Dict con los datos del resumen (se almacenará como JSON)
        
        Returns:
            int: ID del resumen creado o None si hay error
        """
        try:
            # Validar campos requeridos
            if not device_id or not summary_data:
                print("Error: device_id y summary_data son requeridos")
                return None
            
            # Convertir el dict a JSON string
            summary_json = json.dumps(summary_data, ensure_ascii=False, indent=2)
            
            query = """
                INSERT INTO summaries (deviceID, summary)
                VALUES (%s, %s)
            """
            
            params = (device_id, summary_json)
            
            summary_id = mysql_service.execute_insert(query, params)
            if summary_id:
                print(f"Resumen creado exitosamente con ID: {summary_id}")
            return summary_id
            
        except Exception as e:
            print(f"Error creando resumen: {e}")
            return None
    
    def get_summary_by_id(self, summary_id: int) -> Optional[Dict]:
        """
        Obtiene un resumen por su ID
        
        Args:
            summary_id: ID del resumen
            
        Returns:
            Dict con los datos del resumen o None si no existe
        """
        try:
            query = "SELECT * FROM summaries WHERE id = %s"
            results = mysql_service.execute_query(query, (summary_id,))
            
            if results and len(results) > 0:
                result = results[0]
                # Parsear el JSON del summary
                if result.get('summary'):
                    try:
                        result['summary'] = json.loads(result['summary'])
                    except json.JSONDecodeError:
                        print(f"Error parseando JSON del resumen {summary_id}")
                        result['summary'] = {}
                return result
            return None
            
        except Exception as e:
            print(f"Error obteniendo resumen por ID: {e}")
            return None
    
    def get_summaries_by_device_id(self, device_id: str, limit: int = 50) -> List[Dict]:
        """
        Obtiene todos los resúmenes de un device_id específico
        
        Args:
            device_id: ID del dispositivo
            limit: Número máximo de resúmenes a retornar
            
        Returns:
            Lista de resúmenes del dispositivo
        """
        try:
            query = "SELECT * FROM summaries WHERE deviceID = %s ORDER BY created_at DESC LIMIT %s"
            results = mysql_service.execute_query(query, (device_id, limit))
            
            if results:
                # Parsear el JSON de cada summary
                for result in results:
                    if result.get('summary'):
                        try:
                            result['summary'] = json.loads(result['summary'])
                        except json.JSONDecodeError:
                            print(f"Error parseando JSON del resumen {result.get('id')}")
                            result['summary'] = {}
            
            return results or []
            
        except Exception as e:
            print(f"Error obteniendo resúmenes por device_id: {e}")
            return []
    
    def get_latest_summary_by_device_id(self, device_id: str) -> Optional[Dict]:
        """
        Obtiene el resumen más reciente de un device_id específico
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Dict con el resumen más reciente o None si no existe
        """
        try:
            query = "SELECT * FROM summaries WHERE deviceID = %s ORDER BY created_at DESC LIMIT 1"
            results = mysql_service.execute_query(query, (device_id,))
            
            if results and len(results) > 0:
                result = results[0]
                # Parsear el JSON del summary
                if result.get('summary'):
                    try:
                        result['summary'] = json.loads(result['summary'])
                    except json.JSONDecodeError:
                        print(f"Error parseando JSON del resumen {result.get('id')}")
                        result['summary'] = {}
                return result
            return None
            
        except Exception as e:
            print(f"Error obteniendo último resumen por device_id: {e}")
            return None
    
    def update_summary(self, summary_id: int, summary_data: Dict) -> bool:
        """
        Actualiza un resumen existente
        
        Args:
            summary_id: ID del resumen a actualizar
            summary_data: Dict con los nuevos datos del resumen
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Convertir el dict a JSON string
            summary_json = json.dumps(summary_data, ensure_ascii=False, indent=2)
            
            query = "UPDATE summaries SET summary = %s WHERE id = %s"
            
            success = mysql_service.execute_update(query, (summary_json, summary_id))
            if success:
                print(f"Resumen {summary_id} actualizado exitosamente")
            return success
            
        except Exception as e:
            print(f"Error actualizando resumen: {e}")
            return False
    
    def delete_summary(self, summary_id: int) -> bool:
        """
        Elimina un resumen por su ID
        
        Args:
            summary_id: ID del resumen a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        try:
            query = "DELETE FROM summaries WHERE id = %s"
            success = mysql_service.execute_update(query, (summary_id,))
            
            if success:
                print(f"Resumen {summary_id} eliminado exitosamente")
            return success
            
        except Exception as e:
            print(f"Error eliminando resumen: {e}")
            return False
    
    def delete_summaries_by_device_id(self, device_id: str) -> bool:
        """
        Elimina todos los resúmenes de un device_id específico
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            bool: True si se eliminaron correctamente, False en caso contrario
        """
        try:
            query = "DELETE FROM summaries WHERE deviceID = %s"
            success = mysql_service.execute_update(query, (device_id,))
            
            if success:
                print(f"Resúmenes del device_id {device_id} eliminados exitosamente")
            return success
            
        except Exception as e:
            print(f"Error eliminando resúmenes por device_id: {e}")
            return False
    
    def get_all_summaries(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Obtiene todos los resúmenes con paginación
        
        Args:
            limit: Número máximo de resúmenes a retornar
            offset: Número de resúmenes a saltar
            
        Returns:
            Lista de resúmenes
        """
        try:
            query = "SELECT * FROM summaries ORDER BY created_at DESC LIMIT %s OFFSET %s"
            results = mysql_service.execute_query(query, (limit, offset))
            
            if results:
                # Parsear el JSON de cada summary
                for result in results:
                    if result.get('summary'):
                        try:
                            result['summary'] = json.loads(result['summary'])
                        except json.JSONDecodeError:
                            print(f"Error parseando JSON del resumen {result.get('id')}")
                            result['summary'] = {}
            
            return results or []
            
        except Exception as e:
            print(f"Error obteniendo todos los resúmenes: {e}")
            return []
    
    def search_summaries_by_content(self, search_term: str) -> List[Dict]:
        """
        Busca resúmenes por contenido en el JSON
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de resúmenes que contienen el término
        """
        try:
            query = """
                SELECT * FROM summaries 
                WHERE JSON_SEARCH(summary, 'all', %s) IS NOT NULL
                ORDER BY created_at DESC
            """
            
            search_pattern = f"%{search_term}%"
            results = mysql_service.execute_query(query, (search_pattern,))
            
            if results:
                # Parsear el JSON de cada summary
                for result in results:
                    if result.get('summary'):
                        try:
                            result['summary'] = json.loads(result['summary'])
                        except json.JSONDecodeError:
                            print(f"Error parseando JSON del resumen {result.get('id')}")
                            result['summary'] = {}
            
            return results or []
            
        except Exception as e:
            print(f"Error buscando resúmenes por contenido: {e}")
            return []

# Instancia global del servicio de resúmenes
summary_service = SummaryService()