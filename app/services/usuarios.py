
def GetUsuarioById(id: str, conn):
    row = conn.execute("""SELECT r.nombre AS rol, d.nombre AS departamento, u.nombre AS nombre, u.apellido1 AS apellido1, u.apellido2 AS apellido2, u.rut AS rut, u.correo AS correo, u.fecha_nacimiento AS fecha_nacimiento
                        FROM usuarios u 
                        JOIN roles r ON u.rol_id = r.id
                        JOIN departamentos d ON u.departamento_id = d.id 
                        WHERE u.id = %s""", (id,)).fetchall()
    return row