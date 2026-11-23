
def obtenerUsuarioPorId(id: str, conn):
    try:
        row = conn.execute("""SELECT r.nombre AS rol, d.nombre AS departamento, u.nombre AS nombre, u.apellido1 AS apellido1, u.apellido2 AS apellido2, u.rut AS rut, u.correo AS correo, u.fecha_nacimiento AS fecha_nacimiento
                            FROM usuarios u 
                            JOIN roles r ON u.rol_id = r.id
                            JOIN departamentos d ON u.departamento_id = d.id 
                            WHERE u.id = %s""", (id,)).fetchall()
        return row
    except Exception as e:
        return None

def crearUsuario(usuario: dict, conn):
    try:
        conn.execute("""INSERT INTO usuarios (nombre, apellido1, apellido2, rut, correo, fecha_nacimiento, rol_id, departamento_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""", (usuario['nombre'], usuario['apellido1'], usuario['apellido2'], usuario['rut'], usuario['correo'], usuario['fecha_nacimiento'], usuario['rol_id'], usuario['departamento_id']))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False
    
def actualizarUsuario(id: str, usuario: dict, conn):
    try:
        conn.execute("""UPDATE usuarios 
                        SET nombre = COALESCE(%s, nombre), 
                        apellido1 = COALESCE(%s, apellido1), 
                        apellido2 = COALESCE(%s, apellido2), 
                        rut = COALESCE(%s, rut), 
                        correo = COALESCE(%s, correo), 
                        fecha_nacimiento = COALESCE(%s, fecha_nacimiento), 
                        rol_id = COALESCE(%s, rol_id), 
                        departamento_id = COALESCE(%s, departamento_id)
                        WHERE id = %s""", (usuario['nombre'], usuario['apellido1'], usuario['apellido2'], usuario['rut'], usuario['correo'], usuario['fecha_nacimiento'], usuario['rol_id'], usuario['departamento_id'], id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False

def eliminarUsuario(id: str, conn):
    try:
        conn.execute("""DELETE FROM usuarios WHERE id = %s""", (id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return False