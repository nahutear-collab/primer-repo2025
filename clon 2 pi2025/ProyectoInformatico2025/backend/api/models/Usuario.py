from api import app, mysql
from flask import request, jsonify
import jwt
import datetime
from werkzeug.security import check_password_hash, generate_password_hash

class Usuario():
    """
    Clase que representa a un usuario y contiene métodos relacionados con la autenticación.
    """

    def __init__(self, data):
        self._id_usuario = data['id_usuario']
        self._nombre = data['nombre']
        self._correo = data['correo']
        # El ID de negocio a veces no viene en todas las consultas, manejamos con cuidado
        self._id_negocio = data.get('id_negocio')

    def to_json(self):
        return {
            'id_usuario': self._id_usuario,
            'nombre': self._nombre,
            'correo': self._correo,
            'id_negocio': self._id_negocio
        }
    
    @classmethod
    def create(cls, data):
        """
        Método para registrar un nuevo usuario (Usado por usuario_routes.py)
        """
        pwd_hash = generate_password_hash(data['contraseña'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuario (nombre, correo, contraseña, id_negocio) VALUES (%s, %s, %s, %s)",
                    (data['nombre'], data['correo'], pwd_hash, data['id_negocio']))
        mysql.connection.commit()
        cur.close()
        return {"mensaje": "Usuario registrado"}

    @staticmethod
    def login():
        """
        Método estático para la autenticación de usuarios.
        """
        try:
            # Recibo el request del front (Basic Auth)
            auth = request.authorization
            
            if not auth or not auth.username or not auth.password:
                 # Fallback: intentar leer del JSON si no viene en header Authorization
                data = request.get_json(silent=True)
                if data and 'username' in data and 'password' in data:
                     # Simular objeto auth simple
                     class AuthStruct: pass
                     auth = AuthStruct()
                     auth.username = data['username']
                     auth.password = data['password']
                else:
                    return jsonify({"message": "Credenciales incompletas"}), 401

            # Control: ¿existe el usuario en la BD?
            cur = mysql.connection.cursor()
            sqlComando = "SELECT contraseña FROM usuario WHERE correo = %s" # Usamos correo para login generalmente, o nombre? Tu JS manda email.
            
            # NOTA: Tu JS login.js manda el email en el campo 'username'. 
            # Ajustamos la query para buscar por correo si es lo que manda el front, o nombre.
            # Si tu sistema usa 'nombre' para login, deja 'nombre'. Si usa email, cambia a 'correo'.
            # Asumiré 'correo' porque en el form dice 'email'.
            cur.execute("SELECT contraseña FROM usuario WHERE correo = %s", (auth.username,))
            data = cur.fetchone()
            cur.close()
            
            if data is None:
                return jsonify({"message": "Usuario no registrado"}), 401

            pwd_encriptada = data['contraseña'] # Al usar DictCursor, accedemos por clave

            if check_password_hash(pwd_encriptada, auth.password):
                cur = mysql.connection.cursor()
                # Buscamos los datos completos
                cur.execute("SELECT id_usuario, nombre, correo, id_negocio FROM usuario WHERE correo = %s", (auth.username,))
                user_data = cur.fetchone()
                cur.close()
                
                usuario = Usuario(user_data)
                
                # Generar Token
                token = jwt.encode({
                    'id_usuario': usuario._id_usuario,
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=100)
                }, app.config['SECRET_KEY']) #, algorithm="HS256"

                usuario_json = usuario.to_json()
                # En versiones nuevas de PyJWT, encode devuelve string, en viejas bytes.
                # Si es bytes, decodificar.
                if isinstance(token, bytes):
                    token = token.decode('utf-8')
                    
                usuario_json['token'] = token
                return jsonify(usuario_json), 200
            else:
                return jsonify({"message":"Contraseña incorrecta"}), 401
        
        except Exception as ex:
            return jsonify({'message': str(ex)}), 500