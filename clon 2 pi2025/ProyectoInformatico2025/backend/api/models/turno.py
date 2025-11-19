from api import mysql

class Turno:
    def __init__(self, row):
        self._id = row['id_turno']
        self._id_profesional = row['id_profesional']
        self._id_cliente = row['id_cliente']
        self._id_servicio = row['id_servicio']
        self._fecha = str(row['fecha']) # Convertir Date a string
        self._hora = str(row['hora'])   # Convertir Time a string
        self._estado = row['estado']

    def to_json(self):
        return {
            "id_turno": self._id,
            "id_profesional": self._id_profesional,
            "id_cliente": self._id_cliente,
            "id_servicio": self._id_servicio,
            "fecha": self._fecha,
            "hora": self._hora,
            "estado": self._estado
        }

    @classmethod
    def get_all(cls):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM turno")
        rows = cur.fetchall()
        cur.close()
        return [cls(row).to_json() for row in rows]

    @classmethod
    def create(cls, data):
        cur = mysql.connection.cursor()
        # Verificar conflicto
        cur.execute("SELECT * FROM turno WHERE id_profesional=%s AND fecha=%s AND hora=%s",
                    (data['id_profesional'], data['fecha'], data['hora']))
        if cur.fetchone():
            cur.close()
            raise Exception("El profesional ya tiene un turno en ese horario")

        cur.execute("""
            INSERT INTO turno (id_profesional, id_cliente, id_servicio, fecha, hora, estado) 
            VALUES (%s, %s, %s, %s, %s, 'pendiente')
        """, (data['id_profesional'], data['id_cliente'], data['id_servicio'], data['fecha'], data['hora']))
        mysql.connection.commit()
        cur.close()
        return {"mensaje": "Turno agendado exitosamente"}