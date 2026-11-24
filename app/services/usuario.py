import bcrypt

def obtenerUsuarioPorId(id: str, conn):
    try:
        row = conn.execute("""SELECT r.nombre AS rol, d.nombre AS departamento, u.nombre AS nombre, u.apellido1 AS apellido1, u.apellido2 AS apellido2, u.rut AS rut, u.correo AS correo, u.fecha_nacimiento AS fecha_nacimiento
                            FROM usuarios u 
                            JOIN roles r ON u.rol_id = r.id
                            JOIN departamentos d ON u.departamento_id = d.id 
                            WHERE u.id = %s""", (id,)).fetchone()
        return row
    except Exception:
        return None

def crearUsuario(usuario: dict, conn):
    password = usuario['contrasenia'].encode('utf-8')
    hash = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
    try:
        password_hash = bcrypt.hashpw(
            usuario["contrasena"].encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        conn.execute("""INSERT INTO usuarios (nombre, apellido1, apellido2, rut, correo, fecha_nacimiento, rol_id, departamento_id, constrasenia)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (usuario['nombre'], usuario['apellido1'], usuario['apellido2'], usuario['rut'],
                         usuario['correo'], usuario['fecha_nacimiento'], usuario['rol_id'],
                         usuario['departamento_id'], password_hash))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    
def actualizarUsuario(id: str, usuario: dict, conn):
    try:
        password_hash = None
        if usuario.get('contrasena'):
            password_hash = bcrypt.hashpw(
                usuario["contrasena"].encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")

        conn.execute("""UPDATE usuarios 
                        SET nombre = COALESCE(%s, nombre), 
                        apellido1 = COALESCE(%s, apellido1), 
                        apellido2 = COALESCE(%s, apellido2), 
                        rut = COALESCE(%s, rut), 
                        correo = COALESCE(%s, correo), 
                        fecha_nacimiento = COALESCE(%s, fecha_nacimiento), 
                        rol_id = COALESCE(%s, rol_id), 
                        departamento_id = COALESCE(%s, departamento_id),
                        constrasenia = COALESCE(%s, constrasenia)
                        WHERE id = %s""",
                        (usuario.get('nombre'), usuario.get('apellido1'), usuario.get('apellido2'),
                         usuario.get('rut'), usuario.get('correo'), usuario.get('fecha_nacimiento'),
                         usuario.get('rol_id'), usuario.get('departamento_id'), password_hash, id))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False

def eliminarUsuario(id: str, conn):
    try:
        conn.execute("""DELETE FROM usuarios WHERE id = %s""", (id,))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False