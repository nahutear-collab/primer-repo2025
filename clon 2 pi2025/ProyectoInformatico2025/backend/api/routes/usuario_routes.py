from api import app, mysql
from flask import jsonify, request
from api.models.usuario import Usuario # Asegúrate que el archivo se llame Usuario.py o cambia esto a usuario
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

# --- Rutas para /api/usuarios (Lista y Crear) ---
@app.route('/api/usuarios', methods=['GET', 'POST'])
def handle_usuarios():
    
    # --- CREAR UN NUEVO USUARIO (POST) ---
    if request.method == 'POST':
        data = request.json
        # Validación básica
        if not data or 'nombre' not in data or 'correo' not in data or 'contrasena' not in data or 'id_negocio' not in data:
            return jsonify({"error": "'nombre', 'correo', 'contrasena' y 'id_negocio' son requeridos"}), 400
            
        # Revisar si el correo ya existe (Consulta directa rápida para no instanciar todo)
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuario WHERE correo = %s", (data['correo'],))
        if cur.fetchone():
            cur.close()
            return jsonify({"error": "El correo electrónico ya está en uso"}), 409
        cur.close()

        try:
            # Preparamos el diccionario que espera el modelo Usuario
            # Nota: El modelo espera 'contraseña' (con ñ) según tu archivo Usuario.py, 
            # pero aquí recibimos 'contrasena'. Ajustamos los datos antes de crear.
            data_model = {
                'id_usuario': None, # Es autoincremental
                'nombre': data['nombre'],
                'correo': data['correo'],
                'contraseña': data['contrasena'], # Pasamos la pass cruda, el método create del modelo la hashea
                'id_negocio': data['id_negocio']
            }
            
            # Usamos el método create estático del modelo (recomendado según tu estructura)
            # Ojo: Tu modelo Usuario.create ya hace el hash y el insert.
            result = Usuario.create(data_model)
            return jsonify(result), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # --- OBTENER TODOS LOS USUARIOS (GET) ---
    elif request.method == 'GET':
        try:
            # No tienes un método get_all en Usuario.py, hay que implementarlo o hacerlo manual aquí.
            # Lo haré manual usando mysql para que funcione ya mismo.
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM usuario")
            rows = cur.fetchall()
            cur.close()
            # Convertimos filas a objetos Usuario y luego a JSON
            usuarios = [Usuario(row).to_json() for row in rows]
            return jsonify(usuarios), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# --- Rutas para /api/usuarios/<id> (Uno Específico) ---
@app.route('/api/usuarios/<int:id_usuario>', methods=['GET', 'PUT', 'DELETE'])
def handle_usuario_by_id(id_usuario):
    
    # Verificar existencia
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuario WHERE id_usuario = %s", (id_usuario,))
    row = cur.fetchone()
    cur.close()

    if not row:
        return jsonify({"error": "Usuario no encontrado"}), 404

    usuario_obj = Usuario(row)

    # --- OBTENER UN USUARIO (GET) ---
    if request.method == 'GET':
        return jsonify(usuario_obj.to_json()), 200

    # --- ACTUALIZAR UN USUARIO (PUT) ---
    if request.method == 'PUT':
        data = request.json
        try:
            nombre = data.get('nombre', row['nombre'])
            correo = data.get('correo', row['correo'])
            id_negocio = data.get('id_negocio', row['id_negocio'])
            
            # Validar correo duplicado si cambió
            if correo != row['correo']:
                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM usuario WHERE correo = %s", (correo,))
                if cur.fetchone():
                    cur.close()
                    return jsonify({"error": "El correo ya está en uso"}), 409
                cur.close()

            # Actualizar contraseña si viene
            if 'contrasena' in data:
                pwd_hash = generate_password_hash(data['contrasena'])
                cur = mysql.connection.cursor()
                cur.execute("""
                    UPDATE usuario SET nombre=%s, correo=%s, id_negocio=%s, contraseña=%s 
                    WHERE id_usuario=%s
                """, (nombre, correo, id_negocio, pwd_hash, id_usuario))
            else:
                cur = mysql.connection.cursor()
                cur.execute("""
                    UPDATE usuario SET nombre=%s, correo=%s, id_negocio=%s 
                    WHERE id_usuario=%s
                """, (nombre, correo, id_negocio, id_usuario))
            
            mysql.connection.commit()
            cur.close()
            return jsonify({"mensaje": "Usuario actualizado"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # --- BORRAR UN USUARIO (DELETE) ---
    if request.method == 'DELETE':
        try:
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM usuario WHERE id_usuario = %s", (id_usuario,))
            mysql.connection.commit()
            cur.close()
            return jsonify({"mensaje": "Usuario eliminado exitosamente"}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# --- Ruta de Autenticación (Login) ---
# Reemplaza al archivo api/routes/Login.py
@app.route('/login', methods=['POST'])
def login():
    # Usar JSON del body en lugar de auth headers (más común en SPAs modernas)
    data = request.get_json()
    
    # Soporte dual: header Authorization o JSON body (para compatibilidad con tu front)
    auth = request.authorization
    username = ""
    password = ""

    if auth:
        username = auth.username
        password = auth.password
    elif data and 'username' in data and 'password' in data:
        username = data['username'] # Tu front envía 'username' con el email
        password = data['password']
    else:
        return jsonify({"message": "Credenciales incompletas"}), 401

    try:
        cur = mysql.connection.cursor()
        # Buscamos por correo (tu front manda el email en el campo username)
        cur.execute("SELECT * FROM usuario WHERE correo = %s", (username,))
        user_data = cur.fetchone()
        cur.close()

        if not user_data:
            return jsonify({"message": "Usuario no registrado"}), 401

        # Verificar contraseña
        if check_password_hash(user_data['contraseña'], password):
            # Generar Token
            token = jwt.encode({
                'id_usuario': user_data['id_usuario'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=100)
            }, app.config['SECRET_KEY'], algorithm="HS256") # Agregado algoritmo explícito

            usuario_obj = Usuario(user_data)
            resp_json = usuario_obj.to_json()
            resp_json['token'] = token # PyJWT 2.x devuelve string, no bytes
            
            return jsonify(resp_json), 200
        else:
            return jsonify({"message": "Contraseña incorrecta"}), 401

    except Exception as ex:
        return jsonify({'message': str(ex)}), 500