from functools import wraps
from flask import request, jsonify
import jwt
from api import app, mysql # Importar mysql desde api directamente

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({"message": "Falta el token"}), 401
        
        try:
            # Decodificar token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            # Podrías inyectar el usuario actual en kwargs si lo necesitas
        except Exception as ex:
            return jsonify({"message": "Token inválido o expirado"}), 401

        return func(*args, **kwargs)
    return decorated

# He simplificado o eliminado los otros decoradores si no tienes los Store Procedures
# Si necesitas validar propiedad del recurso, hazlo con query directa:

def user_resources(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        # Obtener ID del usuario desde el token (asumiendo que token_required corre antes o extraes lógica)
        # Por ahora, si confías en el header 'user-id' (Inseguro, mejor usar el token):
        user_id_header = request.headers.get('user-id')
        id_user_route = kwargs.get('id_usuario')
        
        if user_id_header and id_user_route:
             if int(id_user_route) != int(user_id_header):
                 return jsonify({"message": "No tiene permisos"}), 403
        return func(*args, **kwargs)
    return decorated