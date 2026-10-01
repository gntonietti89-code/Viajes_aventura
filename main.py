"""Viajes Aventura: clases del diagrama UML oficial y punto de partida del programa.

Ejecutar con:  python main.py
"""

import hashlib
import hmac
import os
import secrets
from datetime import date, datetime, timedelta

DURACION_SESION = timedelta(minutes=30)
ITERACIONES = 200_000

# Estados de una reserva.
PENDIENTE = "pendiente"
PAGADA = "pagada"
CANCELADA = "cancelada"

# Estados de un paquete.
BORRADOR = "borrador"
PUBLICADO = "publicado"
MIN_DESTINOS = 2
MAX_DESTINOS = 5


class Sesion:
    """Sesión abierta por un usuario. Composición: Usuario 1 -> 0..* Sesion."""

    def __init__(self, usuario, ahora):
        self.__token = secrets.token_hex(16)
        self.__expiraEn = ahora + DURACION_SESION
        self.__usuario = usuario
        self.__cerrada = False

    def esValida(self, ahora: datetime) -> bool:
        return not self.__cerrada and ahora < self.__expiraEn

    def getUsuario(self):
        return self.__usuario

    def cerrar(self) -> None:
        self.__cerrada = True


class Usuario:
    """Clase padre de Cliente y Administrador."""

    def __init__(self, id, nombre, correo, clave, contrasenaHash=None):
        self.__id = id
        self.__nombre = nombre
        self.__correo = correo
        # R10: la contraseña nunca se guarda tal como se escribió.
        self.__contrasenaHash = contrasenaHash or self.__hashear(clave)
        self.__sesiones = []

    def getId(self):
        return self.__id

    def asignarId(self, id):
        self.__id = id

    def getNombre(self) -> str:
        return self.__nombre

    def getCorreo(self) -> str:
        return self.__correo

    def getContrasenaHash(self) -> str:
        return self.__contrasenaHash

    def verificarContrasena(self, clave: str) -> bool:
        sal_hex, hash_guardado = self.__contrasenaHash.split("$")
        hash_nuevo = self.__calcularHash(clave, bytes.fromhex(sal_hex))
        return hmac.compare_digest(hash_nuevo, hash_guardado)

    def iniciarSesion(self, clave: str):
        """Devuelve una Sesion si la clave es correcta; si no, None."""
        if not self.verificarContrasena(clave):
            return None
        sesion = Sesion(self, datetime.now())
        self.__sesiones.append(sesion)
        return sesion

    def __hashear(self, clave: str) -> str:
        sal = os.urandom(16)
        return sal.hex() + "$" + self.__calcularHash(clave, sal)

    @staticmethod
    def __calcularHash(clave: str, sal: bytes) -> str:
        return hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, ITERACIONES).hex()


class Cliente(Usuario):
    """Hereda de Usuario."""

    def __init__(self, id, nombre, correo, clave, rut, telefono, contrasenaHash=None):
        super().__init__(id, nombre, correo, clave, contrasenaHash)
        self.__rut = rut
        self.__telefono = telefono
        # Composición: Cliente 1 -> 0..* Reserva ("realiza").
        self.__reservas = []

    def getRut(self) -> str:
        return self.__rut

    def getTelefono(self) -> str:
        return self.__telefono

    def getRutEnmascarado(self) -> str:
        return self.__enmascarar(self.__rut)

    def getTelefonoEnmascarado(self) -> str:
        return self.__enmascarar(self.__telefono)

    def agregarReserva(self, reserva) -> None:
        self.__reservas.append(reserva)

    def quitarReserva(self, reserva) -> None:
        if reserva in self.__reservas:
            self.__reservas.remove(reserva)

    def listarMisReservas(self, sesion) -> list:
        # R11: solo un cliente autenticado ve sus reservas, y únicamente las suyas.
        if not sesion.esValida(datetime.now()) or sesion.getUsuario() is not self:
            raise PermissionError("Sesión no válida para consultar estas reservas.")
        # Se entrega una copia para que nadie modifique la lista interna desde fuera.
        return list(self.__reservas)

    @staticmethod
    def __enmascarar(texto: str) -> str:
        # R17: el RUT y el teléfono no se muestran completos; solo los 3 últimos caracteres.
        return "*" * (len(texto) - 3) + texto[-3:]


class Destino:

    def __init__(self, id, nombre, zona, descripcion, duracionDias, costoBase, disponible=True,
                 fechaActualizacion=None):
        # R2: el costo base siempre es mayor que cero.
        if costoBase <= 0:
            raise ValueError("El costo base debe ser mayor que cero.")
        self.__id = id
        self.__nombre = nombre
        self.__zona = zona
        self.__descripcion = descripcion
        self.__duracionDias = duracionDias
        self.__costoBase = costoBase
        self.__disponible = disponible
        self.__fechaActualizacion = fechaActualizacion or date.today()

    def getId(self):
        return self.__id

    def asignarId(self, id):
        self.__id = id

    def getNombre(self) -> str:
        return self.__nombre

    def getZona(self) -> str:
        return self.__zona

    def getDescripcion(self) -> str:
        return self.__descripcion

    def getDuracionDias(self) -> int:
        return self.__duracionDias

    def getCostoBase(self) -> int:
        return self.__costoBase

    def getFechaActualizacion(self) -> date:
        return self.__fechaActualizacion

    def actualizarCostoBase(self, nuevoCosto: int) -> bool:
        # R2: el costo base siempre es mayor que cero.
        if nuevoCosto <= 0:
            return False
        self.__costoBase = nuevoCosto
        self.__fechaActualizacion = date.today()
        return True

    def marcarNoDisponible(self) -> None:
        self.__disponible = False

    def estaDisponible(self) -> bool:
        return self.__disponible


class Reserva:
    """Una reserva corresponde a un cliente y a un paquete (R12)."""

    def __init__(self, id, fechaEmision, cantidadPersonas, totalCobrado, cliente, paquete, estado=PENDIENTE):
        self.__id = id
        self.__fechaEmision = fechaEmision
        self.__cantidadPersonas = cantidadPersonas
        # R13: el total se fija al reservar y no tiene método para cambiarlo.
        self.__totalCobrado = totalCobrado
        self.__estado = estado
        self.__cliente = cliente
        # Asociación: Reserva 0..* -> 1 Paquete ("es sobre").
        self.__paquete = paquete

    def getId(self):
        return self.__id

    def asignarId(self, id):
        self.__id = id

    def getFechaEmision(self):
        return self.__fechaEmision

    def getCliente(self):
        return self.__cliente

    def getTotal(self) -> int:
        return self.__totalCobrado

    def getEstado(self) -> str:
        return self.__estado

    def getCantidadPersonas(self) -> int:
        # No está en el UML: Paquete lo necesita para calcular el cupo disponible (R14).
        return self.__cantidadPersonas

    def getPaquete(self):
        # No está en el UML: la interfaz lo usa para mostrar el nombre del paquete reservado.
        return self.__paquete

    def marcarPagada(self) -> None:
        if self.__estado == PENDIENTE:
            self.__estado = PAGADA

    def cancelar(self) -> None:
        self.__estado = CANCELADA


class Paquete:

    def __init__(self, id, nombre, fechaSalida, fechaRegreso, cupoMaximo, margen,
                 destinos=None, estado=BORRADOR, precioPorPersona=0):
        # R5: el regreso es posterior a la salida y el cupo es mayor que cero.
        # R6: el margen nunca es negativo.
        if fechaRegreso <= fechaSalida:
            raise ValueError("La fecha de regreso debe ser posterior a la de salida.")
        if cupoMaximo <= 0:
            raise ValueError("El cupo máximo debe ser mayor que cero.")
        if margen < 0:
            raise ValueError("El margen no puede ser negativo.")
        self.__id = id
        self.__nombre = nombre
        self.__fechaSalida = fechaSalida
        self.__fechaRegreso = fechaRegreso
        self.__cupoMaximo = cupoMaximo
        # Margen como fracción: 0.20 equivale a 20 % (R6).
        self.__margen = margen
        self.__precioPorPersona = precioPorPersona
        self.__estado = estado
        # Agregación: Paquete 0..* -> 2..5 Destino ("combina").
        self.__destinos = list(destinos) if destinos else []
        # Lado Paquete de la asociación con Reserva ("es sobre").
        self.__reservas = []

    def getId(self):
        return self.__id

    def asignarId(self, id):
        self.__id = id

    def getNombre(self) -> str:
        # No está en el UML: la interfaz lo usa para listar los paquetes.
        return self.__nombre

    def getFechaSalida(self) -> date:
        # No está en el UML: la interfaz lo usa para listar los paquetes.
        return self.__fechaSalida

    def getFechaRegreso(self) -> date:
        return self.__fechaRegreso

    def getCupoMaximo(self) -> int:
        return self.__cupoMaximo

    def getMargen(self) -> float:
        return self.__margen

    def getEstado(self) -> str:
        return self.__estado

    def getDestinos(self) -> list:
        return list(self.__destinos)

    def agregarReservaPersistida(self, reserva) -> None:
        self.__reservas.append(reserva)

    def quitarReservaPersistida(self, reserva) -> None:
        if reserva in self.__reservas:
            self.__reservas.remove(reserva)

    def agregarDestino(self, destino) -> bool:
        # R3: de 2 a 5 destinos, sin repetir. R8: solo destinos disponibles.
        # Un paquete publicado ya no cambia sus destinos (R7).
        if (self.__estado != BORRADOR
                or len(self.__destinos) >= MAX_DESTINOS
                or destino in self.__destinos
                or not destino.estaDisponible()):
            return False
        self.__destinos.append(destino)
        return True

    def contieneDestino(self, destino) -> bool:
        # No está en el UML: Catalogo lo necesita para saber si puede eliminar un destino (R8).
        return destino in self.__destinos

    def quitarReservaNoPersistida(self, reserva) -> None:
        self.quitarReservaPersistida(reserva)

    def publicar(self) -> bool:
        if self.__estado != BORRADOR or len(self.__destinos) < MIN_DESTINOS:
            return False
        # R7: el precio queda fijado al publicar.
        self.__precioPorPersona = self.__calcularPrecio()
        self.__estado = PUBLICADO
        return True

    def getPrecioPorPersona(self) -> int:
        return self.__precioPorPersona

    def getCupoDisponible(self) -> int:
        # R14: cupo máximo menos las personas ya reservadas (sin contar las canceladas).
        reservadas = sum(r.getCantidadPersonas() for r in self.__reservas
                         if r.getEstado() != CANCELADA)
        return self.__cupoMaximo - reservadas

    def estaVigente(self, hoy) -> bool:
        # R15: un paquete cuya fecha de salida ya pasó no se ofrece.
        return self.__estado == PUBLICADO and self.__fechaSalida > hoy

    def reservar(self, cliente, personas: int, hoy):
        """Crea la reserva si se cumplen R14, R15 y R16; si no, lanza ValueError."""
        if not self.estaVigente(hoy):
            raise ValueError("El paquete no está disponible para reservar.")
        if personas < 1:
            raise ValueError("La reserva debe ser al menos para 1 persona.")
        if personas > self.getCupoDisponible():
            raise ValueError("No hay cupo suficiente en el paquete.")
        # R13: total = precio del paquete x cantidad de personas.
        reserva = Reserva(None, hoy, personas, self.__precioPorPersona * personas, cliente, self)
        self.__reservas.append(reserva)
        cliente.agregarReserva(reserva)
        return reserva

    def __calcularPrecio(self) -> int:
        # R6: suma de los costos base de los destinos, más el margen.
        suma = sum(d.getCostoBase() for d in self.__destinos)
        return round(suma * (1 + self.__margen))


class Catalogo:

    def __init__(self):
        # Composición: Catalogo 1 -> 0..* Destino ("contiene") y 1 -> 0..* Paquete ("ofrece").
        self.__destinos = []
        self.__paquetes = []

    def registrarDestino(self, destino) -> bool:
        # R1: el nombre del destino no se repite en el catálogo.
        nombre = destino.getNombre().strip().lower()
        if any(d.getNombre().strip().lower() == nombre for d in self.__destinos):
            return False
        self.__destinos.append(destino)
        return True

    def retirarDestino(self, destino) -> None:
        # R8: si está en algún paquete, se marca no disponible; si no, se elimina.
        if any(p.contieneDestino(destino) for p in self.__paquetes):
            destino.marcarNoDisponible()
        elif destino in self.__destinos:
            self.__destinos.remove(destino)

    def listarDestinosDisponibles(self) -> list:
        return [d for d in self.__destinos if d.estaDisponible()]

    def agregarPaquete(self, paquete) -> None:
        self.__paquetes.append(paquete)

    def retirarPaquete(self, paquete) -> None:
        if paquete in self.__paquetes:
            self.__paquetes.remove(paquete)

    def destinoIncluidoEnPaquete(self, destino) -> bool:
        return any(paquete.contieneDestino(destino) for paquete in self.__paquetes)

    def listarPaquetesVigentes(self, hoy) -> list:
        return [p for p in self.__paquetes if p.estaVigente(hoy)]


class Administrador(Usuario):
    """Hereda de Usuario."""

    def __init__(self, id, nombre, correo, clave, catalogo, contrasenaHash=None):
        super().__init__(id, nombre, correo, clave, contrasenaHash)
        # Asociación: Administrador 1..* -> 1 Catalogo ("mantiene").
        self.__catalogo = catalogo

    def crearPaquete(self, nombre, salida, regreso, cupo, margen) -> Paquete:
        paquete = Paquete(None, nombre, salida, regreso, cupo, margen)
        self.__catalogo.agregarPaquete(paquete)
        return paquete

    def marcarReservaPagada(self, reserva) -> None:
        reserva.marcarPagada()


if __name__ == "__main__":
    from interface import iniciar
    iniciar()
