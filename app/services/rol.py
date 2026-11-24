def obtenerRoles(conn):
    try:
        rows = conn.execute("""SELECT id, nombre FROM roles ORDER BY id""").fetchall()
        return rows
    except Exception as e:
        print(e)
        return None

def obtenerRolPorId(id: int, conn):
    try:
        row = conn.execute("""SELECT id, nombre FROM roles WHERE id = %s""", (id,)).fetchone()
        return row
    except Exception as e:
        print(e)
        return None

def crearRol(rol: dict, conn):
    try:
        conn.execute("""INSERT INTO roles (nombre) VALUES (%s)""", (rol['nombre'],))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        return False

def actualizarRol(id: int, rol: dict, conn):
    try:
        conn.execute("""UPDATE roles SET nombre = %s WHERE id = %s""", (rol['nombre'], id))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        return False

def eliminarRol(id: int, conn):
    try:
        conn.execute("""DELETE FROM roles WHERE id = %s""", (id,))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        return False
