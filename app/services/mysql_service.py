import os
import mysql.connector
from mysql.connector import Error
import json
from typing import Optional, Dict, List, Any
from datetime import datetime

class MySQLService:
    def __init__(self):
        self.connection = None
        self.host = os.getenv('CONTACT_DB_HOST', 'localhost')
        self.port = int(os.getenv('CONTACT_DB_PORT', 3306))
        self.user = os.getenv('CONTACT_DB_USER')
        self.password = os.getenv('CONTACT_DB_PASSWORD')
        self.database = os.getenv('CONTACT_DB_NAME')
        
    def connect(self):
        """Establece conexión con la base de datos MySQL"""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    autocommit=True
                )
                print(f"Conexión exitosa a MySQL: {self.database}")
            return self.connection
        except Error as e:
            print(f"Error conectando a MySQL: {e}")
            return None
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexión MySQL cerrada")
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """Ejecuta una consulta SELECT y retorna los resultados"""
        try:
            connection = self.connect()
            if not connection:
                return None
                
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"Error ejecutando consulta: {e}")
            return None
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """Ejecuta una consulta INSERT y retorna el ID insertado"""
        try:
            connection = self.connect()
            if not connection:
                return None
                
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        except Error as e:
            print(f"Error ejecutando INSERT: {e}")
            return None
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Ejecuta una consulta UPDATE/DELETE y retorna si fue exitosa"""
        try:
            connection = self.connect()
            if not connection:
                return False
                
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows > 0
        except Error as e:
            print(f"Error ejecutando UPDATE/DELETE: {e}")
            return False

# Instancia global del servicio MySQL
mysql_service = MySQLService()