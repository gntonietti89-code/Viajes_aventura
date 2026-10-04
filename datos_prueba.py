"""Carga datos de prueba en viajes_aventura.db (clientes, destinos, paquetes y reservas).

Usa las mismas clases y la misma base de datos que el programa, así se respetan sus reglas.
Se puede ejecutar varias veces: lo que ya existe (mismo correo o nombre) no se duplica.
Uso: python datos_prueba.py
"""

from datetime import date, timedelta

import interface
from database import BaseDatos
from main import Administrador, Cliente, Destino

CLAVE_PRUEBA = "Prueba123"
ADMIN_NOMBRE = "admin"
ADMIN_CORREO = "admin@gmail.com"
ADMIN_CLAVE = "admin1234"

CLIENTES = [
    ("Ana Rojas", "ana@prueba.cl", "11111111-1", "+56911111111"),
    ("Benjamín Soto", "benja@prueba.cl", "22222222-2", "+56922222222"),
    ("Carla Muñoz", "carla@prueba.cl", "12345678-5", "+56933333333"),
]

SAN_PEDRO = "San Pedro de Atacama"
PUERTO_VARAS = "Puerto Varas"
TORRES_DEL_PAINE = "Torres del Paine"
CHILOE = "Chiloé"

DESTINOS = [
    # nombre, zona, descripción, días, costo base por persona
    (SAN_PEDRO, "Norte", "Desierto, géiseres del Tatio y valle de la Luna", 4, 180000),
    ("Valle del Elqui", "Norte Chico", "Observatorios, pisco y cielos despejados", 3, 95000),
    ("Isla de Pascua", "Insular", "Moáis, playa Anakena y cultura Rapa Nui", 5, 450000),
    (PUERTO_VARAS, "Sur", "Lago Llanquihue, volcán Osorno y saltos del Petrohué", 3, 120000),
    (TORRES_DEL_PAINE, "Patagonia", "Trekking al mirador de las Torres y glaciar Grey", 5, 320000),
    (CHILOE, "Sur", "Iglesias de madera, palafitos y curanto", 3, 110000),
]

HOY = date.today()

PAQUETES = [
    # nombre, días hasta la salida, duración, cupo, margen, destinos
    ("Norte Mágico", 30, 7, 20, 0.20, [SAN_PEDRO, "Valle del Elqui"]),
    ("Sur de Lagos", 60, 6, 10, 0.15, [PUERTO_VARAS, CHILOE]),
    ("Gran Chile", 90, 14, 4, 0.25,
     [SAN_PEDRO, "Isla de Pascua", PUERTO_VARAS, TORRES_DEL_PAINE, CHILOE]),
    # Borrador: solo 1 destino, no se puede publicar ni reservar.
    ("Patagonia Express (borrador)", 45, 5, 8, 0.10, [TORRES_DEL_PAINE]),
]

RESERVAS = [
    # correo del cliente, paquete, personas
    ("ana@prueba.cl", "Norte Mágico", 2),
    ("benja@prueba.cl", "Sur de Lagos", 4),
    ("carla@prueba.cl", "Gran Chile", 3),  # deja 1 cupo libre para probar el límite
]


def cargar_administrador(bd):
    """Crea la cuenta de demostración si todavía no está registrada."""
    existente = interface.buscar_usuario(ADMIN_CORREO)
    if existente:
        if not isinstance(existente, Administrador):
            raise ValueError(f"El correo {ADMIN_CORREO} ya está registrado como cliente.")
        print(f"Administrador de demostración: {ADMIN_CORREO} (ya existía)")
        return

    admin = Administrador(None, ADMIN_NOMBRE, ADMIN_CORREO, ADMIN_CLAVE, interface.catalogo)
    admin.asignarId(bd.crear_usuario(
        admin.getNombre(), admin.getCorreo(), admin.getContrasenaHash(), "administrador",
    ))
    interface.usuarios.append(admin)
    print(f"Administrador de demostración: {ADMIN_CORREO}")


def cargar_clientes(bd):
    for nombre, correo, rut, telefono in CLIENTES:
        if interface.buscar_usuario(correo):
            continue
        assert interface.validar_rut(rut), rut
        cliente = Cliente(None, nombre, correo, CLAVE_PRUEBA, rut, telefono)
        cliente.asignarId(bd.crear_usuario(nombre, correo, cliente.getContrasenaHash(), "cliente",
                                           rut, telefono))
        interface.usuarios.append(cliente)
        print(f"Cliente: {correo}")


def cargar_destinos(bd, catalogo):
    """Devuelve todos los destinos disponibles por nombre, incluidos los recién creados."""
    destinos = {d.getNombre(): d for d in catalogo.listarDestinosDisponibles()}
    for nombre, zona, descripcion, dias, costo in DESTINOS:
        if nombre in destinos:
            continue
        destino = Destino(None, nombre, zona, descripcion, dias, costo)
        if catalogo.registrarDestino(destino):
            destino.asignarId(bd.crear_destino(
                nombre, zona, descripcion, dias, costo, destino.estaDisponible(),
                destino.getFechaActualizacion().isoformat(),
            ))
            destinos[nombre] = destino
            print(f"Destino: {nombre}")
    return destinos


def cargar_paquetes(bd, destinos):
    """Devuelve solo los paquetes creados en esta ejecución, por nombre."""
    admin = next(u for u in interface.usuarios if isinstance(u, Administrador))
    existentes = {p["nombre"] for p in bd.listar_paquetes()}
    paquetes = {}
    for nombre, dias_hasta, duracion, cupo, margen, nombres_destinos in PAQUETES:
        if nombre in existentes:
            continue
        salida = HOY + timedelta(days=dias_hasta)
        paquete = admin.crearPaquete(nombre, salida, salida + timedelta(days=duracion), cupo, margen)
        paquete.asignarId(bd.crear_paquete(
            nombre, salida.isoformat(), paquete.getFechaRegreso().isoformat(), cupo, margen,
            paquete.getPrecioPorPersona(), paquete.getEstado(),
        ))
        for posicion, nombre_destino in enumerate(nombres_destinos):
            destino = destinos[nombre_destino]
            if paquete.agregarDestino(destino):
                bd.vincular_destino_paquete(paquete.getId(), destino.getId(), posicion)
        paquete.publicar()
        interface.guardar_paquete(paquete)
        paquetes[nombre] = paquete
        print(f"Paquete: {nombre} ({paquete.getEstado()}, "
              f"{interface.pesos(paquete.getPrecioPorPersona())} por persona)")
    return paquetes


def cargar_reservas(bd, paquetes):
    for correo, nombre_paquete, personas in RESERVAS:
        paquete = paquetes.get(nombre_paquete)
        if paquete is None:  # el paquete ya existía: su reserva se creó antes
            continue
        cliente = interface.buscar_usuario(correo)
        reserva = paquete.reservar(cliente, personas, HOY)
        reserva.asignarId(bd.crear_reserva(
            reserva.getFechaEmision().isoformat(), personas, reserva.getTotal(),
            reserva.getEstado(), cliente.getId(), paquete.getId(),
        ))
        print(f"Reserva: {correo} -> {nombre_paquete}, {personas} persona(s), "
              f"{interface.pesos(reserva.getTotal())}")


def cargar():
    bd = interface.base_datos
    cargar_administrador(bd)
    cargar_clientes(bd)
    destinos = cargar_destinos(bd, interface.catalogo)
    paquetes = cargar_paquetes(bd, destinos)
    cargar_reservas(bd, paquetes)


if __name__ == "__main__":
    interface.base_datos = BaseDatos()
    try:
        interface.cargar_datos()
        cargar()
        print(f"\nListo. Administrador: {ADMIN_CORREO} / {ADMIN_CLAVE}")
        print(f"Contraseña de los clientes de prueba: {CLAVE_PRUEBA}")
    finally:
        interface.base_datos.cerrar()
