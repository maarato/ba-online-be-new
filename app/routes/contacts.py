from flask import Blueprint, request, jsonify
from app.services.contact_service import contact_service

contacts_bp = Blueprint('contacts', __name__, url_prefix='/api/contacts')

@contacts_bp.route('/', methods=['POST'])
def create_contact():
    """
    Crear un nuevo contacto
    
    Body JSON esperado:
    {
        "nombre": "string (requerido)",
        "apellido": "string (requerido)", 
        "email": "string (requerido)",
        "job_title": "string (opcional)",
        "company": "string (opcional)",
        "interested_in": "string (opcional)",
        "more_details": "string (opcional)",
        "device_id": "string (opcional)"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        # Validar campos requeridos
        required_fields = ['nombre', 'apellido', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'El campo {field} es requerido'}), 400
        
        contact_id = contact_service.create_contact(data)
        
        if contact_id:
            return jsonify({
                'message': 'Contacto creado exitosamente',
                'contact_id': contact_id
            }), 201
        else:
            return jsonify({'error': 'Error creando el contacto'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@contacts_bp.route('/<int:contact_id>', methods=['GET'])
def get_contact(contact_id):
    """Obtener un contacto por ID"""
    try:
        contact = contact_service.get_contact_by_id(contact_id)
        
        if contact:
            return jsonify(contact), 200
        else:
            return jsonify({'error': 'Contacto no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@contacts_bp.route('/email/<email>', methods=['GET'])
def get_contact_by_email(email):
    """Obtener un contacto por email"""
    try:
        contact = contact_service.get_contact_by_email(email)
        
        if contact:
            return jsonify(contact), 200
        else:
            return jsonify({'error': 'Contacto no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@contacts_bp.route('/device/<device_id>', methods=['GET'])
def get_contacts_by_device(device_id):
    """Obtener todos los contactos de un dispositivo"""
    try:
        contacts = contact_service.get_contacts_by_device_id(device_id)
        
        return jsonify({
            'contacts': contacts,
            'count': len(contacts)
        }), 200
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@contacts_bp.route('/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """
    Actualizar un contacto existente
    
    Body JSON con los campos a actualizar:
    {
        "nombre": "string (opcional)",
        "apellido": "string (opcional)", 
        "email": "string (opcional)",
        "job_title": "string (opcional)",
        "company": "string (opcional)",
        "interested_in": "string (opcional)",
        "more_details": "string (opcional)",
        "device_id": "string (opcional)"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos para actualizar'}), 400
        
        # Verificar que el contacto existe
        existing_contact = contact_service.get_contact_by_id(contact_id)
        if not existing_contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        success = contact_service.update_contact(contact_id, data)
        
        if success:
            return jsonify({'message': 'Contacto actualizado exitosamente'}), 200
        else:
            return jsonify({'error': 'Error actualizando el contacto'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@contacts_bp.route('/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Eliminar un contacto por ID"""
    try:
        # Verificar que el contacto existe
        existing_contact = contact_service.get_contact_by_id(contact_id)
        if not existing_contact:
            return jsonify({'error': 'Contacto no encontrado'}), 404
        
        success = contact_service.delete_contact(contact_id)
        
        if success:
            return jsonify({'message': 'Contacto eliminado exitosamente'}), 200
        else:
            return jsonify({'error': 'Error eliminando el contacto'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@contacts_bp.route('/', methods=['GET'])
def get_all_contacts():
    """
    Obtener todos los contactos con paginación
    
    Query parameters:
    - limit: número máximo de contactos (default: 100)
    - offset: número de contactos a saltar (default: 0)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validar límites
        if limit > 1000:
            limit = 1000
        if limit < 1:
            limit = 1
        if offset < 0:
            offset = 0
        
        contacts = contact_service.get_all_contacts(limit, offset)
        
        return jsonify({
            'contacts': contacts,
            'count': len(contacts),
            'limit': limit,
            'offset': offset
        }), 200
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@contacts_bp.route('/search', methods=['GET'])
def search_contacts():
    """
    Buscar contactos por término
    
    Query parameters:
    - q: término de búsqueda (requerido)
    """
    try:
        search_term = request.args.get('q')
        
        if not search_term:
            return jsonify({'error': 'Parámetro de búsqueda "q" es requerido'}), 400
        
        contacts = contact_service.search_contacts(search_term)
        
        return jsonify({
            'contacts': contacts,
            'count': len(contacts),
            'search_term': search_term
        }), 200
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500