"""Persistencia SQLite para Viajes Aventura."""

import sqlite3
from pathlib import Path


class BaseDatos:
    """Conexión y operaciones CRUD para las entidades del sistema."""

    def __init__(self, ruta=None):
        self.__ruta = Path(ruta) if ruta else Path(__file__).with_name("viajes_aventura.db")
        self.__conexion = sqlite3.connect(self.__ruta)
        self.__conexion.row_factory = sqlite3.Row
        try:
            self.__conexion.execute("PRAGMA foreign_keys = ON")
            self.__crear_tablas()
        except sqlite3.Error:
            self.__conexion.close()
            raise

    def __crear_tablas(self):
        self.__conexion.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL COLLATE NOCASE UNIQUE,
                contrasena_hash TEXT NOT NULL,
                rol TEXT NOT NULL,
                rut TEXT,
                telefono TEXT
            );
            CREATE TABLE IF NOT EXISTS destinos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL COLLATE NOCASE UNIQUE,
                zona TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                duracion_dias INTEGER NOT NULL,
                costo_base INTEGER NOT NULL,
                disponible INTEGER NOT NULL,
                fecha_actualizacion TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS paquetes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                fecha_salida TEXT NOT NULL,
                fecha_regreso TEXT NOT NULL,
                cupo_maximo INTEGER NOT NULL,
                margen REAL NOT NULL,
                precio_por_persona INTEGER NOT NULL,
                estado TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS paquete_destinos (
                paquete_id INTEGER NOT NULL REFERENCES paquetes(id) ON DELETE CASCADE,
                destino_id INTEGER NOT NULL REFERENCES destinos(id) ON DELETE RESTRICT,
                posicion INTEGER NOT NULL,
                PRIMARY KEY (paquete_id, destino_id)
            );
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_emision TEXT NOT NULL,
                cantidad_personas INTEGER NOT NULL,
                total_cobrado INTEGER NOT NULL,
                estado TEXT NOT NULL,
                cliente_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
                paquete_id INTEGER NOT NULL REFERENCES paquetes(id) ON DELETE RESTRICT
            );
            """
        )
        self.__conexion.commit()

    @staticmethod
    def __filas(cursor):
        return [dict(fila) for fila in cursor.fetchall()]

    def cerrar(self):
        self.__conexion.close()

    def crear_usuario(self, nombre, correo, contrasena_hash, rol, rut=None, telefono=None):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "INSERT INTO usuarios (nombre, correo, contrasena_hash, rol, rut, telefono) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (nombre, correo, contrasena_hash, rol, rut, telefono),
            )
        return cursor.lastrowid

    def listar_usuarios(self):
        return self.__filas(self.__conexion.execute("SELECT * FROM usuarios ORDER BY id"))

    def actualizar_usuario(self, id_usuario, nombre, correo, contrasena_hash, rol, rut=None, telefono=None):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "UPDATE usuarios SET nombre=?, correo=?, contrasena_hash=?, rol=?, rut=?, telefono=? "
                "WHERE id=?",
                (nombre, correo, contrasena_hash, rol, rut, telefono, id_usuario),
            )
        return cursor.rowcount

    def eliminar_usuario(self, id_usuario):
        with self.__conexion:
            cursor = self.__conexion.execute("DELETE FROM usuarios WHERE id=?", (id_usuario,))
        return cursor.rowcount

    def crear_destino(self, nombre, zona, descripcion, duracion_dias, costo_base, disponible, fecha_actualizacion):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "INSERT INTO destinos (nombre, zona, descripcion, duracion_dias, costo_base, disponible, "
                "fecha_actualizacion) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nombre, zona, descripcion, duracion_dias, costo_base, int(disponible), fecha_actualizacion),
            )
        return cursor.lastrowid

    def listar_destinos(self):
        return self.__filas(self.__conexion.execute("SELECT * FROM destinos ORDER BY id"))

    def actualizar_destino(self, id_destino, nombre, zona, descripcion, duracion_dias, costo_base, disponible,
                           fecha_actualizacion):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "UPDATE destinos SET nombre=?, zona=?, descripcion=?, duracion_dias=?, costo_base=?, "
                "disponible=?, fecha_actualizacion=? WHERE id=?",
                (nombre, zona, descripcion, duracion_dias, costo_base, int(disponible), fecha_actualizacion,
                 id_destino),
            )
        return cursor.rowcount

    def eliminar_destino(self, id_destino):
        with self.__conexion:
            cursor = self.__conexion.execute("DELETE FROM destinos WHERE id=?", (id_destino,))
        return cursor.rowcount

    def crear_paquete(self, nombre, fecha_salida, fecha_regreso, cupo_maximo, margen, precio_por_persona, estado):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "INSERT INTO paquetes (nombre, fecha_salida, fecha_regreso, cupo_maximo, margen, "
                "precio_por_persona, estado) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (nombre, fecha_salida, fecha_regreso, cupo_maximo, margen, precio_por_persona, estado),
            )
        return cursor.lastrowid

    def listar_paquetes(self):
        return self.__filas(self.__conexion.execute("SELECT * FROM paquetes ORDER BY id"))

    def actualizar_paquete(self, id_paquete, nombre, fecha_salida, fecha_regreso, cupo_maximo, margen,
                           precio_por_persona, estado):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "UPDATE paquetes SET nombre=?, fecha_salida=?, fecha_regreso=?, cupo_maximo=?, margen=?, "
                "precio_por_persona=?, estado=? WHERE id=?",
                (nombre, fecha_salida, fecha_regreso, cupo_maximo, margen, precio_por_persona, estado, id_paquete),
            )
        return cursor.rowcount

    def eliminar_paquete(self, id_paquete):
        with self.__conexion:
            cursor = self.__conexion.execute("DELETE FROM paquetes WHERE id=?", (id_paquete,))
        return cursor.rowcount

    def vincular_destino_paquete(self, id_paquete, id_destino, posicion):
        with self.__conexion:
            self.__conexion.execute(
                "INSERT INTO paquete_destinos (paquete_id, destino_id, posicion) VALUES (?, ?, ?)",
                (id_paquete, id_destino, posicion),
            )

    def listar_destinos_de_paquete(self, id_paquete):
        return self.__filas(self.__conexion.execute(
            "SELECT d.* FROM destinos d JOIN paquete_destinos pd ON pd.destino_id=d.id "
            "WHERE pd.paquete_id=? ORDER BY pd.posicion",
            (id_paquete,),
        ))

    def crear_reserva(self, fecha_emision, cantidad_personas, total_cobrado, estado, cliente_id, paquete_id):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "INSERT INTO reservas (fecha_emision, cantidad_personas, total_cobrado, estado, cliente_id, "
                "paquete_id) VALUES (?, ?, ?, ?, ?, ?)",
                (fecha_emision, cantidad_personas, total_cobrado, estado, cliente_id, paquete_id),
            )
        return cursor.lastrowid

    def listar_reservas(self):
        return self.__filas(self.__conexion.execute("SELECT * FROM reservas ORDER BY id"))

    def actualizar_reserva(self, id_reserva, fecha_emision, cantidad_personas, total_cobrado, estado, cliente_id,
                           paquete_id):
        with self.__conexion:
            cursor = self.__conexion.execute(
                "UPDATE reservas SET fecha_emision=?, cantidad_personas=?, total_cobrado=?, estado=?, cliente_id=?, "
                "paquete_id=? WHERE id=?",
                (fecha_emision, cantidad_personas, total_cobrado, estado, cliente_id, paquete_id, id_reserva),
            )
        return cursor.rowcount

    def eliminar_reserva(self, id_reserva):
        with self.__conexion:
            cursor = self.__conexion.execute("DELETE FROM reservas WHERE id=?", (id_reserva,))
        return cursor.rowcount