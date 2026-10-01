"""Menú de consola de Viajes Aventura.

Los datos se guardan en SQLite (database.py) y se cargan al iniciar el programa.
"""

from datetime import date, datetime
from getpass import getpass
import re
import sqlite3
import sys
import unicodedata

from database import BaseDatos
from main import Administrador, Catalogo, Cliente, Destino, Paquete, Reserva

catalogo = Catalogo()
usuarios = []  # Clientes y administradores registrados.
base_datos = None


class VolverMenu(Exception):
    """Señal para cancelar la acción actual y regresar al menú anterior."""


VOLVER_MENU = object()
FINALIZAR_MENU = object()


def cargar_datos():
    """Reconstruye el catálogo y sus relaciones desde SQLite."""
    global catalogo, usuarios
    catalogo = Catalogo()
    usuarios = []
    usuarios_por_id = {}
    destinos_por_id = {}
    paquetes_por_id = {}

    for fila in base_datos.listar_usuarios():
        if fila["rol"] == "cliente":
            usuario = Cliente(fila["id"], fila["nombre"], fila["correo"], "", fila["rut"],
                              fila["telefono"], fila["contrasena_hash"])
        else:
            usuario = Administrador(fila["id"], fila["nombre"], fila["correo"], "", catalogo,
                                    fila["contrasena_hash"])
        usuarios.append(usuario)
        usuarios_por_id[fila["id"]] = usuario

    for fila in base_datos.listar_destinos():
        destino = Destino(fila["id"], fila["nombre"], fila["zona"], fila["descripcion"],
                          fila["duracion_dias"], fila["costo_base"], bool(fila["disponible"]),
                          date.fromisoformat(fila["fecha_actualizacion"]))
        catalogo.registrarDestino(destino)
        destinos_por_id[fila["id"]] = destino

    for fila in base_datos.listar_paquetes():
        destinos = [destinos_por_id[d["id"]]
                    for d in base_datos.listar_destinos_de_paquete(fila["id"])]
        paquete = Paquete(
            fila["id"], fila["nombre"], date.fromisoformat(fila["fecha_salida"]),
            date.fromisoformat(fila["fecha_regreso"]), fila["cupo_maximo"], fila["margen"],
            destinos, fila["estado"], fila["precio_por_persona"],
        )
        catalogo.agregarPaquete(paquete)
        paquetes_por_id[fila["id"]] = paquete

    for fila in base_datos.listar_reservas():
        cliente = usuarios_por_id[fila["cliente_id"]]
        paquete = paquetes_por_id[fila["paquete_id"]]
        reserva = Reserva(
            fila["id"], date.fromisoformat(fila["fecha_emision"]), fila["cantidad_personas"],
            fila["total_cobrado"], cliente, paquete, fila["estado"],
        )
        cliente.agregarReserva(reserva)
        paquete.agregarReservaPersistida(reserva)


# ---------- Sanitización ----------

LARGO_TEXTO = 100        # nombre, zona, etc.
LARGO_DESCRIPCION = 500
LARGO_CORREO = 254       # máximo del estándar de correo
CLAVE_MIN = 8
CLAVE_MAX = 64           # evita que una clave enorme vuelva lento el hash
COSTO_MAX = 50_000_000
DURACION_MAX = 60
CUPO_MAX = 100
MARGEN_MAX = 100


def limpiar_texto(texto):
    """Quita caracteres de control (p. ej. códigos ANSI), une espacios repetidos y normaliza acentos."""
    texto = unicodedata.normalize("NFC", texto)
    texto = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", texto)  # secuencias ANSI completas
    texto = "".join(" " if c.isspace() else c for c in texto
                    if c.isspace() or unicodedata.category(c)[0] != "C")
    return " ".join(texto.split())


def validar_rut(texto):
    """Devuelve el RUT como 12345678-9 si el dígito verificador (módulo 11) es correcto; si no, None."""
    rut = texto.replace(".", "").replace("-", "").replace(" ", "").upper()
    if not re.fullmatch(r"\d{7,8}[\dK]", rut):
        return None
    cuerpo, dv = rut[:-1], rut[-1]
    suma = sum(int(d) * f for d, f in zip(reversed(cuerpo), [2, 3, 4, 5, 6, 7] * 2))
    esperado = {10: "K", 11: "0"}.get(11 - suma % 11, str(11 - suma % 11))
    return f"{cuerpo}-{dv}" if dv == esperado else None


def validar_telefono(texto):
    """Acepta un celular chileno (+56 9 1234 5678 o 912345678) y lo devuelve como +56912345678."""
    numero = re.sub(r"[\s\-()]", "", texto)
    if re.fullmatch(r"(\+?56)?9\d{8}", numero):
        return "+56" + numero[-9:]
    return None


# ---------- Ayudas para pedir datos ----------

def pedir_texto(mensaje, largo_maximo=LARGO_TEXTO):
    while True:
        texto_ingresado = input(mensaje + " (/volver para regresar): ").strip()
        if texto_ingresado.casefold() == "/volver":
            raise VolverMenu
        texto = limpiar_texto(texto_ingresado)
        if not texto:
            print("  No puede quedar vacío.")
        elif len(texto) > largo_maximo:
            print(f"  Máximo {largo_maximo} caracteres.")
        else:
            return texto


def pedir_correo(mensaje="Correo: "):
    while True:
        correo = pedir_texto(mensaje, LARGO_CORREO).lower()
        if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
            return correo
        print("  Ingrese un correo con formato válido.")


def leer_tecla():
    """Lee una tecla sin mostrarla en pantalla (Windows, Linux o macOS)."""
    try:
        import msvcrt
        return msvcrt.getwch()
    except ImportError:
        import termios
        import tty
        descriptor = sys.stdin.fileno()
        anterior = termios.tcgetattr(descriptor)
        try:
            tty.setraw(descriptor)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(descriptor, termios.TCSADRAIN, anterior)


def leer_clave(mensaje):
    """Pide la contraseña mostrando un * por cada carácter, sin revelar lo escrito."""
    if not sys.stdin.isatty():
        clave = getpass(mensaje + " (/volver para regresar): ")
        if clave == "/volver":
            raise VolverMenu
        return clave  # entrada redirigida: no hay teclado donde mostrar asteriscos
    print(mensaje + " (Esc para regresar): ", end="", flush=True)
    clave = ""
    while True:
        tecla = leer_tecla()
        if tecla == "\x1b":
            print()
            raise VolverMenu
        if tecla in ("\r", "\n"):
            print()
            return clave
        if tecla == "\x03":  # Ctrl+C
            raise KeyboardInterrupt
        if tecla in ("\x00", "\xe0"):  # flechas y teclas especiales en Windows
            leer_tecla()
        elif tecla in ("\b", "\x7f"):  # borrar
            if clave:
                clave = clave[:-1]
                print("\b \b", end="", flush=True)
        elif tecla.isprintable() and len(clave) < CLAVE_MAX + 1:
            clave += tecla
            print("*", end="", flush=True)


def pedir_clave(mensaje="Contraseña: ", validar_largo=True):
    """Al registrar se exige el largo; al iniciar sesión solo que no esté vacía."""
    while True:
        clave = leer_clave(mensaje)
        if not clave.strip():
            print("  La contraseña no puede quedar vacía.")
        elif len(clave) > CLAVE_MAX:
            print(f"  La contraseña puede tener como máximo {CLAVE_MAX} caracteres.")
        elif validar_largo and len(clave) < CLAVE_MIN:
            print(f"  La contraseña debe tener al menos {CLAVE_MIN} caracteres.")
        else:
            return clave


def pedir_clave_nueva():
    """Para crear una cuenta: pide la contraseña dos veces y exige que coincidan."""
    while True:
        clave = pedir_clave()
        if leer_clave("Confirmar contraseña: ") == clave:
            return clave
        print("  Las contraseñas no coinciden. Inténtelo de nuevo.")


def pedir_rut(mensaje="RUT (ej. 19616711-0): "):
    while True:
        rut = validar_rut(pedir_texto(mensaje, 12))
        if rut:
            return rut
        print("  RUT no válido. Escríbalo sin puntos y con guion, ej. 19616711-0")


def pedir_telefono(mensaje="Teléfono (ej. +56912345678): "):
    while True:
        telefono = validar_telefono(pedir_texto(mensaje, 20))
        if telefono:
            return telefono
        print("  Teléfono no válido. Escríbalo sin espacios, ej. +56912345678")


def pedir_entero(mensaje, minimo=0, maximo=None):
    while True:
        texto = input(mensaje + " (/volver para regresar): ").strip()
        if texto.casefold() == "/volver":
            raise VolverMenu
        # Se limita el largo antes de convertir para no procesar números gigantes.
        if not (texto.isascii() and texto.isdecimal()) or len(texto) > 12:
            print("  Debe ingresar un número entero no negativo.")
            continue
        valor = int(texto)
        if valor < minimo:
            print(f"  El valor debe ser mayor o igual que {minimo}.")
        elif maximo is not None and valor > maximo:
            print(f"  El valor debe ser menor o igual que {maximo}.")
        else:
            return valor


def pedir_fecha(mensaje):
    while True:
        texto = input(mensaje + " (dd-mm-aaaa, /volver para regresar): ").strip()
        if texto.casefold() == "/volver":
            raise VolverMenu
        try:
            return datetime.strptime(texto, "%d-%m-%Y").date()
        except ValueError:
            print("  Fecha no válida.")


def ejecutar_accion(accion, *args):
    """Evita que un fallo de almacenamiento cierre el menú y oculta detalles internos."""
    try:
        return accion(*args)
    except VolverMenu:
        print("  Acción cancelada. Volviendo al menú anterior.")
    except sqlite3.Error:
        print("  No se pudo completar la operación por un problema de almacenamiento.")
    except (OSError, OverflowError):
        print("  No se pudo acceder al almacenamiento local.")


def elegir(lista, describir):
    """Muestra una lista numerada y devuelve el elemento elegido, o None si se cancela."""
    if not lista:
        print("  No hay elementos para mostrar.")
        return None
    opciones = {str(i): describir(elemento) for i, elemento in enumerate(lista, start=1)}
    opcion = leer_opcion_menu("Elija un elemento", opciones, texto_volver="Cancelar")
    if opcion is VOLVER_MENU:
        raise VolverMenu
    return lista[int(opcion) - 1] if opcion is not None else None


def leer_opcion_menu(titulo, opciones, texto_volver="Volver"):
    """Muestra y valida opciones; todo menú obtiene la misma salida de regreso."""
    while True:
        print(f"\n--- {titulo} ---")
        for clave, descripcion in opciones.items():
            print(f"{clave}. {descripcion}")
        print(f"0. {texto_volver}")
        opcion = input("> ").strip()
        if opcion.casefold() == "/volver":
            return VOLVER_MENU
        if opcion == "0":
            return None
        if opcion in opciones:
            return opcion
        print("  Opción no válida. Elija una opción del menú o 0 para volver.")


def ejecutar_menu(titulo, opciones, texto_volver="Volver"):
    """Despacha opciones con el mismo comportamiento de navegación en cualquier menú."""
    while True:
        opcion = leer_opcion_menu(
            titulo,
            {clave: descripcion for clave, (descripcion, _accion, _args) in opciones.items()},
            texto_volver,
        )
        if opcion is None or opcion is VOLVER_MENU:
            return
        _descripcion, accion, argumentos = opciones[opcion]
        resultado = ejecutar_accion(accion, *argumentos)
        if resultado is FINALIZAR_MENU:
            return


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
    correo = pedir_correo()
    # R9: el correo identifica al cliente y no se repite.
    if buscar_usuario(correo):
        print("  Ese correo ya está registrado.")
        return
    nombre = pedir_texto("Nombre: ")
    rut = pedir_rut()
    telefono = pedir_telefono()
    clave = pedir_clave_nueva()
    cliente = Cliente(None, nombre, correo, clave, rut, telefono)
    cliente.asignarId(base_datos.crear_usuario(
        nombre, correo, cliente.getContrasenaHash(), "cliente", rut, telefono,
    ))
    usuarios.append(cliente)
    print("  Cliente registrado.")


def iniciar_sesion():
    print("\nInicio de sesión")
    correo = pedir_correo()
    clave = pedir_clave(validar_largo=False)
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
    personas = pedir_entero("Cantidad de personas: ", minimo=1, maximo=CUPO_MAX)
    try:
        reserva = paquete.reservar(cliente, personas, date.today())
        try:
            reserva.asignarId(base_datos.crear_reserva(
                reserva.getFechaEmision().isoformat(), reserva.getCantidadPersonas(), reserva.getTotal(),
                reserva.getEstado(), cliente.getId(), paquete.getId(),
            ))
        except sqlite3.Error:
            paquete.quitarReservaNoPersistida(reserva)
            cliente.quitarReserva(reserva)
            raise
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
                      pedir_texto("Descripción: ", LARGO_DESCRIPCION),
                      pedir_entero("Duración en días: ", minimo=1, maximo=DURACION_MAX),
                      pedir_entero("Costo base por persona: ", minimo=1, maximo=COSTO_MAX))
    if catalogo.registrarDestino(destino):
        try:
            destino.asignarId(base_datos.crear_destino(
                destino.getNombre(), destino.getZona(), destino.getDescripcion(), destino.getDuracionDias(),
                destino.getCostoBase(), destino.estaDisponible(), destino.getFechaActualizacion().isoformat(),
            ))
        except sqlite3.Error:
            catalogo.retirarDestino(destino)
            raise
        print("  Destino registrado.")
    else:
        print("  Ya existe un destino con ese nombre.")


def retirar_destino():
    print("\nRetirar destino")
    destino = elegir(catalogo.listarDestinosDisponibles(), lambda d: d.getNombre())
    if destino:
        if catalogo.destinoIncluidoEnPaquete(destino):
            actualizado = base_datos.actualizar_destino(
                destino.getId(), destino.getNombre(), destino.getZona(), destino.getDescripcion(),
                destino.getDuracionDias(), destino.getCostoBase(), False,
                destino.getFechaActualizacion().isoformat(),
            )
        else:
            actualizado = base_datos.eliminar_destino(destino.getId())
        if actualizado:
            catalogo.retirarDestino(destino)
            print("  Destino retirado del catálogo.")
        else:
            print("  No se pudo encontrar el destino en la base de datos.")


def guardar_destino(destino):
    base_datos.actualizar_destino(
        destino.getId(), destino.getNombre(), destino.getZona(), destino.getDescripcion(),
        destino.getDuracionDias(), destino.getCostoBase(), destino.estaDisponible(),
        destino.getFechaActualizacion().isoformat(),
    )


def actualizar_costo_destino():
    print("\nActualizar costo base")
    destino = elegir(catalogo.listarDestinosDisponibles(), lambda d: d.getNombre())
    if destino is None:
        return
    nuevo_costo = pedir_entero("Nuevo costo base por persona: ", minimo=1, maximo=COSTO_MAX)
    actualizado = base_datos.actualizar_destino(
        destino.getId(), destino.getNombre(), destino.getZona(), destino.getDescripcion(),
        destino.getDuracionDias(), nuevo_costo, destino.estaDisponible(), date.today().isoformat(),
    )
    if actualizado and destino.actualizarCostoBase(nuevo_costo):
        print("  Costo actualizado.")
    elif not actualizado:
        print("  No se pudo encontrar el destino en la base de datos.")
    else:
        print("  El costo base debe ser mayor que cero.")


def crear_paquete(admin):
    print("\nNuevo paquete")
    nombre = pedir_texto("Nombre: ")
    salida = pedir_fecha("Fecha de salida")
    while salida <= date.today():
        print("  La fecha de salida debe ser posterior a hoy.")
        salida = pedir_fecha("Fecha de salida")
    regreso = pedir_fecha("Fecha de regreso")
    while regreso <= salida:
        print("  La fecha de regreso debe ser posterior a la salida.")
        regreso = pedir_fecha("Fecha de regreso")
    cupo = pedir_entero("Cupo máximo: ", minimo=1, maximo=CUPO_MAX)
    margen = pedir_entero("Margen en % (ej. 20): ", minimo=0, maximo=MARGEN_MAX) / 100
    paquete = admin.crearPaquete(nombre, salida, regreso, cupo, margen)
    try:
        paquete.asignarId(base_datos.crear_paquete(
            paquete.getNombre(), paquete.getFechaSalida().isoformat(), paquete.getFechaRegreso().isoformat(),
            paquete.getCupoMaximo(), paquete.getMargen(), paquete.getPrecioPorPersona(), paquete.getEstado(),
        ))
        print("Elija de 2 a 5 destinos (0 para terminar):")
        while True:
            destino = elegir(catalogo.listarDestinosDisponibles(), lambda d: d.getNombre())
            if destino is None:
                break
            if not paquete.agregarDestino(destino):
                print("  No se pudo agregar (repetido o ya hay 5 destinos).")
            else:
                base_datos.vincular_destino_paquete(paquete.getId(), destino.getId(),
                                                    len(paquete.getDestinos()) - 1)
        base_datos.actualizar_paquete(
            paquete.getId(), paquete.getNombre(), paquete.getFechaSalida().isoformat(),
            paquete.getFechaRegreso().isoformat(), paquete.getCupoMaximo(), paquete.getMargen(),
            paquete.getPrecioPorPersona(), paquete.getEstado(),
        )
        if paquete.publicar():
            base_datos.actualizar_paquete(
                paquete.getId(), paquete.getNombre(), paquete.getFechaSalida().isoformat(),
                paquete.getFechaRegreso().isoformat(), paquete.getCupoMaximo(), paquete.getMargen(),
                paquete.getPrecioPorPersona(), paquete.getEstado(),
            )
            print(f"  Paquete publicado a {pesos(paquete.getPrecioPorPersona())} por persona.")
        else:
            print("  El paquete necesita al menos 2 destinos; quedó como borrador.")
    except (sqlite3.Error, VolverMenu):
        catalogo.retirarPaquete(paquete)
        if paquete.getId() is not None:
            try:
                base_datos.eliminar_paquete(paquete.getId())
            except sqlite3.Error:
                pass
        raise


# ---------- Menús ----------

def menu_cliente(cliente, sesion):
    opciones = {
        "1": ("Ver paquetes vigentes", ver_paquetes, ()),
        "2": ("Reservar", reservar, (cliente,)),
        "3": ("Mis reservas", ver_mis_reservas, (cliente, sesion)),
        "4": ("Cerrar sesión", cerrar_sesion_cliente, ()),
    }
    ejecutar_menu("Menú cliente", opciones, "Cerrar sesión y volver")
    sesion.cerrar()


def cerrar_sesion_cliente():
    print("Sesión cerrada. Volviendo al menú principal.")
    return FINALIZAR_MENU


def menu_administrador(admin, sesion):
    opciones = {
        "1": ("Listar destinos", listar_destinos, ()),
        "2": ("Registrar destino", registrar_destino, ()),
        "3": ("Actualizar costo de destino", actualizar_costo_destino, ()),
        "4": ("Retirar destino", retirar_destino, ()),
        "5": ("Crear paquete", crear_paquete, (admin,)),
        "6": ("Ver paquetes vigentes", ver_paquetes, ()),
    }
    ejecutar_menu("Menú administrador", opciones, "Cerrar sesión y volver")
    sesion.cerrar()


def listar_destinos():
    for destino in catalogo.listarDestinosDisponibles():
        print(f"  - {destino.getNombre()} · {pesos(destino.getCostoBase())}")


def crear_administrador_inicial():
    if any(isinstance(usuario, Administrador) for usuario in usuarios):
        return
    print("Primera ejecución: cree la cuenta del administrador.")
    correo = pedir_correo()
    while buscar_usuario(correo):
        print("  Ese correo ya está registrado.")
        correo = pedir_correo()
    admin = Administrador(None, pedir_texto("Nombre: "), correo, pedir_clave_nueva(), catalogo)
    admin.asignarId(base_datos.crear_usuario(
        admin.getNombre(), admin.getCorreo(), admin.getContrasenaHash(), "administrador",
    ))
    usuarios.append(admin)


def iniciar():
    global base_datos
    print("=== Viajes Aventura ===")
    try:
        base_datos = BaseDatos()
        cargar_datos()
        crear_administrador_inicial()
        opciones = {
            "1": ("Ver paquetes vigentes", ver_paquetes, ()),
            "2": ("Registrarse como cliente", registrar_cliente, ()),
            "3": ("Iniciar sesión", iniciar_sesion, ()),
        }
        ejecutar_menu("Menú principal", opciones, "Salir")
        print("Hasta luego.")
    except VolverMenu:
        print("Configuración inicial cancelada. Puede volver a ejecutar el programa.")
    except sqlite3.Error:
        print("No se pudo iniciar o consultar la base de datos. Revise el almacenamiento e intente de nuevo.")
    except (OSError, OverflowError, ValueError, KeyError, TypeError):
        print("No se pudo acceder a la base de datos local.")
    finally:
        if base_datos is not None:
            base_datos.cerrar()
            base_datos = None
