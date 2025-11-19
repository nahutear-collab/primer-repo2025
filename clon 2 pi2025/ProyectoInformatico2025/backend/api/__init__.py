from flask import Flask
from flask_cors import CORS
from flask_mysqldb import MySQL

app = Flask(__name__)
CORS(app)

# Configuración MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'proyecto'
app.config['MYSQL_PASSWORD'] = 'proyecto' 
app.config['MYSQL_DB'] = 'turnos'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = 'supersecreto'

mysql = MySQL(app)

# Esto evita el error circular, ya que las rutas necesitan importar 'app' de aquí.
import api.routes.negocio_routes
import api.routes.cliente_routes
import api.routes.servicio_routes
import api.routes.profesional_routes
import api.routes.usuario_routes
import api.routes.disponibilidad_routes
import api.routes.turno_routes
import api.routes.Login