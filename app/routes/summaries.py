from flask import Blueprint, request, jsonify
from app.services.summary_service import summary_service

summaries_bp = Blueprint('summaries', __name__, url_prefix='/api/summaries')

@summaries_bp.route('/', methods=['POST'])
def create_summary():
    """
    Crear un nuevo resumen
    
    Body JSON esperado:
    {
        "device_id": "string (requerido)",
        "summary": "object (requerido) - Datos del resumen en formato JSON"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos'}), 400
        
        device_id = data.get('device_id')
        summary_data = data.get('summary')
        
        if not device_id:
            return jsonify({'error': 'El campo device_id es requerido'}), 400
        
        if not summary_data:
            return jsonify({'error': 'El campo summary es requerido'}), 400
        
        summary_id = summary_service.create_summary(device_id, summary_data)
        
        if summary_id:
            return jsonify({
                'message': 'Resumen creado exitosamente',
                'summary_id': summary_id
            }), 201
        else:
            return jsonify({'error': 'Error creando el resumen'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/<int:summary_id>', methods=['GET'])
def get_summary(summary_id):
    """Obtener un resumen por ID"""
    try:
        summary = summary_service.get_summary_by_id(summary_id)
        
        if summary:
            return jsonify(summary), 200
        else:
            return jsonify({'error': 'Resumen no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/device/<device_id>', methods=['GET'])
def get_summaries_by_device(device_id):
    """
    Obtener todos los resúmenes de un dispositivo
    
    Query parameters:
    - limit: número máximo de resúmenes (default: 50)
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        
        # Validar límites
        if limit > 200:
            limit = 200
        if limit < 1:
            limit = 1
        
        summaries = summary_service.get_summaries_by_device_id(device_id, limit)
        
        return jsonify({
            'summaries': summaries,
            'count': len(summaries),
            'device_id': device_id,
            'limit': limit
        }), 200
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/device/<device_id>/latest', methods=['GET'])
def get_latest_summary_by_device(device_id):
    """Obtener el resumen más reciente de un dispositivo"""
    try:
        summary = summary_service.get_latest_summary_by_device_id(device_id)
        
        if summary:
            return jsonify(summary), 200
        else:
            return jsonify({'error': 'No se encontraron resúmenes para este dispositivo'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/<int:summary_id>', methods=['PUT'])
def update_summary(summary_id):
    """
    Actualizar un resumen existente
    
    Body JSON esperado:
    {
        "summary": "object (requerido) - Nuevos datos del resumen en formato JSON"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionaron datos para actualizar'}), 400
        
        summary_data = data.get('summary')
        
        if not summary_data:
            return jsonify({'error': 'El campo summary es requerido'}), 400
        
        # Verificar que el resumen existe
        existing_summary = summary_service.get_summary_by_id(summary_id)
        if not existing_summary:
            return jsonify({'error': 'Resumen no encontrado'}), 404
        
        success = summary_service.update_summary(summary_id, summary_data)
        
        if success:
            return jsonify({'message': 'Resumen actualizado exitosamente'}), 200
        else:
            return jsonify({'error': 'Error actualizando el resumen'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/<int:summary_id>', methods=['DELETE'])
def delete_summary(summary_id):
    """Eliminar un resumen por ID"""
    try:
        # Verificar que el resumen existe
        existing_summary = summary_service.get_summary_by_id(summary_id)
        if not existing_summary:
            return jsonify({'error': 'Resumen no encontrado'}), 404
        
        success = summary_service.delete_summary(summary_id)
        
        if success:
            return jsonify({'message': 'Resumen eliminado exitosamente'}), 200
        else:
            return jsonify({'error': 'Error eliminando el resumen'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/device/<device_id>', methods=['DELETE'])
def delete_summaries_by_device(device_id):
    """Eliminar todos los resúmenes de un dispositivo"""
    try:
        success = summary_service.delete_summaries_by_device_id(device_id)
        
        if success:
            return jsonify({'message': f'Resúmenes del dispositivo {device_id} eliminados exitosamente'}), 200
        else:
            return jsonify({'error': 'Error eliminando los resúmenes o no se encontraron resúmenes'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/', methods=['GET'])
def get_all_summaries():
    """
    Obtener todos los resúmenes con paginación
    
    Query parameters:
    - limit: número máximo de resúmenes (default: 100)
    - offset: número de resúmenes a saltar (default: 0)
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validar límites
        if limit > 500:
            limit = 500
        if limit < 1:
            limit = 1
        if offset < 0:
            offset = 0
        
        summaries = summary_service.get_all_summaries(limit, offset)
        
        return jsonify({
            'summaries': summaries,
            'count': len(summaries),
            'limit': limit,
            'offset': offset
        }), 200
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@summaries_bp.route('/search', methods=['GET'])
def search_summaries():
    """
    Buscar resúmenes por contenido
    
    Query parameters:
    - q: término de búsqueda (requerido)
    """
    try:
        search_term = request.args.get('q')
        
        if not search_term:
            return jsonify({'error': 'Parámetro de búsqueda "q" es requerido'}), 400
        
        summaries = summary_service.search_summaries_by_content(search_term)
        
        return jsonify({
            'summaries': summaries,
            'count': len(summaries),
            'search_term': search_term
        }), 200
            
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500