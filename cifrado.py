"""Cifrado de datos sensibles (RUT y teléfono, R17) con Fernet, de la librería cryptography (PyPI).

La llave de cifrado nunca se escribe en el código: se lee de la variable de entorno
VIAJES_CLAVE_CIFRADO o del archivo .env, que está en .gitignore y no se sube al repositorio.
Si no existe, se genera una nueva la primera vez y se guarda en .env.
"""

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

RUTA_ENV = Path(__file__).with_name(".env")
VARIABLE_LLAVE = "VIAJES_CLAVE_CIFRADO"
# Cualquier texto cifrado con Fernet empieza así (versión 0x80 en base64).
PREFIJO_FERNET = "gAAAAA"


class ErrorCifrado(Exception):
    """La llave no es válida o no corresponde a los datos guardados."""


class Cifrador:

    def __init__(self, llave: str):
        try:
            self.__fernet = Fernet(llave.encode())
        except (ValueError, TypeError) as error:
            raise ErrorCifrado("La llave de cifrado no tiene un formato válido.") from error

    def cifrar(self, texto):
        if texto is None:
            return None
        return self.__fernet.encrypt(texto.encode("utf-8")).decode("ascii")

    def descifrar(self, token):
        if token is None:
            return None
        try:
            return self.__fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeError) as error:
            raise ErrorCifrado("No se pudieron descifrar los datos con la llave actual.") from error

    @staticmethod
    def estaCifrado(valor) -> bool:
        return isinstance(valor, str) and valor.startswith(PREFIJO_FERNET)

    @classmethod
    def desdeEntorno(cls):
        """Crea el cifrador con la llave del entorno o de .env; si no hay llave, la genera."""
        load_dotenv(RUTA_ENV)
        llave = os.getenv(VARIABLE_LLAVE)
        if not llave:
            llave = Fernet.generate_key().decode("ascii")
            with open(RUTA_ENV, "a", encoding="utf-8") as archivo:
                archivo.write(f"{VARIABLE_LLAVE}={llave}\n")
            os.environ[VARIABLE_LLAVE] = llave
        return cls(llave)
