"""Menú de consola de Viajes Aventura.

Por ahora los datos viven solo en memoria: se pierden al cerrar el programa.
La base de datos se agrega en el criterio 2.1.3.
"""

from datetime import date, datetime
from getpass import getpass

from main import Administrador, Catalogo, Cliente, Destino

catalogo = Catalogo()
usuarios = []  # Clientes y administradores registrados.


# ---------- Ayudas para pedir datos ----------

def pedir_texto(mensaje):
    texto = input(mensaje).strip()
    while not texto:
        texto = input("  No puede quedar vacío. " + mensaje).strip()
    return texto


def pedir_entero(mensaje):
    texto = input(mensaje).strip()
    while not texto.isdigit():
        texto = input("  Debe ser un número entero. " + mensaje).strip()
    return int(texto)


def pedir_fecha(mensaje):
    while True:
        texto = input(mensaje + " (dd-mm-aaaa): ").strip()
        try:
            return datetime.strptime(texto, "%d-%m-%Y").date()
        except ValueError:
            print("  Fecha no válida.")


def elegir(lista, describir):
    """Muestra una lista numerada y devuelve el elemento elegido, o None si se cancela."""
    if not lista:
        print("  No hay elementos para mostrar.")
        return None
    for i, elemento in enumerate(lista, start=1):
        print(f"  {i}. {describir(elemento)}")
    opcion = pedir_entero("  Elija un número (0 para cancelar): ")
    if 1 <= opcion <= len(lista):
        return lista[opcion - 1]
    return None


def pesos(monto):
    """Formato chileno: $516.000"""
    return "$" + f"{monto:,}".replace(",", ".")


def describir_paquete(p):
    return (f"{p.getNombre()} · sale {p.getFechaSalida():%d-%m-%Y} · "
            f"{pesos(p.getPrecioPorPersona())} por persona · cupo {p.getCupoDisponible()}")


def buscar_usuario(correo):
    for u in usuarios:
        if u.getCorreo().lower() == correo.lower():
            return u
    return None


# ---------- Acciones ----------

def ver_paquetes():
    print("\nPaquetes vigentes:")
    paquetes = catalogo.listarPaquetesVigentes(date.today())
    if not paquetes:
        print("  No hay paquetes vigentes.")
    for p in paquetes:
        print("  - " + describir_paquete(p))


def registrar_cliente():
    print("\nRegistro de cliente")
    correo = pedir_texto("Correo: ")
    # R9: el correo identifica al cliente y no se repite.
    if buscar_usuario(correo):
        print("  Ese correo ya está registrado.")
        return
    nombre = pedir_texto("Nombre: ")
    rut = pedir_texto("RUT: ")
    telefono = pedir_texto("Teléfono: ")
    clave = getpass("Contraseña: ")
    usuarios.append(Cliente(None, nombre, correo, clave, rut, telefono))
    print("  Cliente registrado.")


def iniciar_sesion():
    print("\nInicio de sesión")
    correo = pedir_texto("Correo: ")
    clave = getpass("Contraseña: ")
    usuario = buscar_usuario(correo)
    sesion = usuario.iniciarSesion(clave) if usuario else None
    if sesion is None:
        # Mismo mensaje en ambos casos: no se revela si el correo existe.
        print("  Correo o contraseña incorrectos.")
        return
    print(f"  Bienvenido/a, {usuario.getNombre()}.")
    if isinstance(usuario, Administrador):
        menu_administrador(usuario, sesion)
    else:
        menu_cliente(usuario, sesion)


def reservar(cliente):
    print("\nReservar paquete")
    paquete = elegir(catalogo.listarPaquetesVigentes(date.today()), describir_paquete)
    if paquete is None:
        return
    personas = pedir_entero("Cantidad de personas: ")
    try:
        reserva = paquete.reservar(cliente, personas, date.today())
        print(f"  Reserva creada. Total: {pesos(reserva.getTotal())} (estado: {reserva.getEstado()}).")
    except ValueError as error:
        print("  No se pudo reservar: " + str(error))


def ver_mis_reservas(cliente, sesion):
    print("\nMis reservas")
    try:
        reservas = cliente.listarMisReservas(sesion)
    except PermissionError:
        print("  Su sesión expiró. Inicie sesión de nuevo.")
        return
    if not reservas:
        print("  No tiene reservas.")
    for r in reservas:
        print(f"  - {r.getPaquete().getNombre()} · {r.getCantidadPersonas()} persona(s) · "
              f"{pesos(r.getTotal())} · {r.getEstado()}")


def registrar_destino():
    print("\nNuevo destino")
    destino = Destino(None, pedir_texto("Nombre: "), pedir_texto("Zona: "),
                      pedir_texto("Descripción: "), pedir_entero("Duración en días: "),
                      pedir_entero("Costo base por persona: "))
    if destino.getCostoBase() <= 0:
        print("  El costo base debe ser mayor que cero.")
    elif catalogo.registrarDestino(destino):
        print("  Destino registrado.")
    else:
        print("  Ya existe un destino con ese nombre.")


def retirar_destino():
    print("\nRetirar destino")
    destino = elegir(catalogo.listarDestinosDisponibles(), lambda d: d.getNombre())
    if destino:
        catalogo.retirarDestino(destino)
        print("  Destino retirado del catálogo.")


def crear_paquete(admin):
    print("\nNuevo paquete")
    nombre = pedir_texto("Nombre: ")
    salida = pedir_fecha("Fecha de salida")
    regreso = pedir_fecha("Fecha de regreso")
    cupo = pedir_entero("Cupo máximo: ")
    margen = pedir_entero("Margen en % (ej. 20): ") / 100
    paquete = admin.crearPaquete(nombre, salida, regreso, cupo, margen)
    print("Elija de 2 a 5 destinos (0 para terminar):")
    while True:
        destino = elegir(catalogo.listarDestinosDisponibles(), lambda d: d.getNombre())
        if destino is None:
            break
        if not paquete.agregarDestino(destino):
            print("  No se pudo agregar (repetido o ya hay 5 destinos).")
    if paquete.publicar():
        print(f"  Paquete publicado a {pesos(paquete.getPrecioPorPersona())} por persona.")
    else:
        print("  El paquete necesita al menos 2 destinos; quedó como borrador.")


# ---------- Menús ----------

def menu_cliente(cliente, sesion):
    while True:
        print("\n--- Menú cliente ---")
        print("1. Ver paquetes vigentes\n2. Reservar\n3. Mis reservas\n0. Cerrar sesión")
        opcion = input("> ").strip()
        if opcion == "1":
            ver_paquetes()
        elif opcion == "2":
            reservar(cliente)
        elif opcion == "3":
            ver_mis_reservas(cliente, sesion)
        elif opcion == "0":
            sesion.cerrar()
            return


def menu_administrador(admin, sesion):
    while True:
        print("\n--- Menú administrador ---")
        print("1. Listar destinos\n2. Registrar destino\n3. Retirar destino\n"
              "4. Crear paquete\n5. Ver paquetes vigentes\n0. Cerrar sesión")
        opcion = input("> ").strip()
        if opcion == "1":
            for d in catalogo.listarDestinosDisponibles():
                print(f"  - {d.getNombre()} · {pesos(d.getCostoBase())}")
        elif opcion == "2":
            registrar_destino()
        elif opcion == "3":
            retirar_destino()
        elif opcion == "4":
            crear_paquete(admin)
        elif opcion == "5":
            ver_paquetes()
        elif opcion == "0":
            sesion.cerrar()
            return


def crear_administrador_inicial():
    # No se guardan credenciales en el código: el administrador se crea al iniciar.
    print("Primera ejecución: cree la cuenta del administrador.")
    usuarios.append(Administrador(None, pedir_texto("Nombre: "), pedir_texto("Correo: "),
                                  getpass("Contraseña: "), catalogo))


def iniciar():
    print("=== Viajes Aventura ===")
    crear_administrador_inicial()
    while True:
        print("\n--- Menú principal ---")
        print("1. Ver paquetes vigentes\n2. Registrarse como cliente\n3. Iniciar sesión\n0. Salir")
        opcion = input("> ").strip()
        if opcion == "1":
            ver_paquetes()
        elif opcion == "2":
            registrar_cliente()
        elif opcion == "3":
            iniciar_sesion()
        elif opcion == "0":
            print("Hasta luego.")
            return
