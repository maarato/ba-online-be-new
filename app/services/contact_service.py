from typing import Optional, Dict, List
from datetime import datetime
from .mysql_service import mysql_service

class ContactService:
    
    def create_contact(self, contact_data: Dict) -> Optional[int]:
        """
        Crea un nuevo contacto en la base de datos
        
        Args:
            contact_data: Dict con los campos del contacto
                - nombre (str, requerido)
                - apellido (str, requerido) 
                - email (str, requerido)
                - job_title (str, opcional)
                - company (str, opcional)
                - interested_in (str, opcional)
                - more_details (str, opcional)
                - device_id (str, opcional)
        
        Returns:
            int: ID del contacto creado o None si hay error
        """
        try:
            # Validar campos requeridos
            if not contact_data.get('nombre') or not contact_data.get('apellido') or not contact_data.get('email'):
                print("Error: Faltan campos requeridos (nombre, apellido, email)")
                return None
            
            query = """
                INSERT INTO contactos (nombre, apellido, job_title, company, interested_in, more_details, email, device_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            params = (
                contact_data.get('nombre'),
                contact_data.get('apellido'),
                contact_data.get('job_title'),
                contact_data.get('company'),
                contact_data.get('interested_in'),
                contact_data.get('more_details'),
                contact_data.get('email'),
                contact_data.get('device_id')
            )
            
            contact_id = mysql_service.execute_insert(query, params)
            if contact_id:
                print(f"Contacto creado exitosamente con ID: {contact_id}")
            return contact_id
            
        except Exception as e:
            print(f"Error creando contacto: {e}")
            return None
    
    def get_contact_by_id(self, contact_id: int) -> Optional[Dict]:
        """
        Obtiene un contacto por su ID
        
        Args:
            contact_id: ID del contacto
            
        Returns:
            Dict con los datos del contacto o None si no existe
        """
        try:
            query = "SELECT * FROM contactos WHERE id = %s"
            results = mysql_service.execute_query(query, (contact_id,))
            
            if results and len(results) > 0:
                return results[0]
            return None
            
        except Exception as e:
            print(f"Error obteniendo contacto por ID: {e}")
            return None
    
    def get_contact_by_email(self, email: str) -> Optional[Dict]:
        """
        Obtiene un contacto por su email
        
        Args:
            email: Email del contacto
            
        Returns:
            Dict con los datos del contacto o None si no existe
        """
        try:
            query = "SELECT * FROM contactos WHERE email = %s"
            results = mysql_service.execute_query(query, (email,))
            
            if results and len(results) > 0:
                return results[0]
            return None
            
        except Exception as e:
            print(f"Error obteniendo contacto por email: {e}")
            return None
    
    def get_contacts_by_device_id(self, device_id: str) -> List[Dict]:
        """
        Obtiene todos los contactos de un device_id específico
        
        Args:
            device_id: ID del dispositivo
            
        Returns:
            Lista de contactos del dispositivo
        """
        try:
            query = "SELECT * FROM contactos WHERE device_id = %s ORDER BY created_at DESC"
            results = mysql_service.execute_query(query, (device_id,))
            return results or []
            
        except Exception as e:
            print(f"Error obteniendo contactos por device_id: {e}")
            return []
    
    def update_contact(self, contact_id: int, contact_data: Dict) -> bool:
        """
        Actualiza un contacto existente
        
        Args:
            contact_id: ID del contacto a actualizar
            contact_data: Dict con los campos a actualizar
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Construir query dinámicamente solo con campos presentes
            update_fields = []
            params = []
            
            allowed_fields = ['nombre', 'apellido', 'job_title', 'company', 'interested_in', 'more_details', 'email', 'device_id']
            
            for field in allowed_fields:
                if field in contact_data:
                    update_fields.append(f"{field} = %s")
                    params.append(contact_data[field])
            
            if not update_fields:
                print("No hay campos para actualizar")
                return False
            
            params.append(contact_id)  # Para el WHERE
            
            query = f"UPDATE contactos SET {', '.join(update_fields)} WHERE id = %s"
            
            success = mysql_service.execute_update(query, tuple(params))
            if success:
                print(f"Contacto {contact_id} actualizado exitosamente")
            return success
            
        except Exception as e:
            print(f"Error actualizando contacto: {e}")
            return False
    
    def delete_contact(self, contact_id: int) -> bool:
        """
        Elimina un contacto por su ID
        
        Args:
            contact_id: ID del contacto a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        try:
            query = "DELETE FROM contactos WHERE id = %s"
            success = mysql_service.execute_update(query, (contact_id,))
            
            if success:
                print(f"Contacto {contact_id} eliminado exitosamente")
            return success
            
        except Exception as e:
            print(f"Error eliminando contacto: {e}")
            return False
    
    def get_all_contacts(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Obtiene todos los contactos con paginación
        
        Args:
            limit: Número máximo de contactos a retornar
            offset: Número de contactos a saltar
            
        Returns:
            Lista de contactos
        """
        try:
            query = "SELECT * FROM contactos ORDER BY created_at DESC LIMIT %s OFFSET %s"
            results = mysql_service.execute_query(query, (limit, offset))
            return results or []
            
        except Exception as e:
            print(f"Error obteniendo todos los contactos: {e}")
            return []
    
    def search_contacts(self, search_term: str) -> List[Dict]:
        """
        Busca contactos por nombre, apellido, email o empresa
        
        Args:
            search_term: Término de búsqueda
            
        Returns:
            Lista de contactos que coinciden con la búsqueda
        """
        try:
            query = """
                SELECT * FROM contactos 
                WHERE nombre LIKE %s 
                   OR apellido LIKE %s 
                   OR email LIKE %s 
                   OR company LIKE %s
                ORDER BY created_at DESC
            """
            
            search_pattern = f"%{search_term}%"
            params = (search_pattern, search_pattern, search_pattern, search_pattern)
            
            results = mysql_service.execute_query(query, params)
            return results or []
            
        except Exception as e:
            print(f"Error buscando contactos: {e}")
            return []

# Instancia global del servicio de contactos
contact_service = ContactService()