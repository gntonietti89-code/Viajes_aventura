"""Consumo de servicios externos (Unidad 3): clima de un destino y tipo de cambio.

Usa la librería requests (PyPI). Ninguna de las dos APIs pide llave de acceso:
- Open-Meteo (https://open-meteo.com): ubicación y clima actual.
- mindicador.cl: indicadores económicos del Banco Central de Chile (dólar y euro).
"""

from datetime import datetime
from math import isfinite

import requests

TIEMPO_ESPERA = 10  # segundos; evita que el programa quede esperando a un servicio caído


class ErrorServicioExterno(Exception):
    """La consulta falló o el servicio devolvió datos no válidos."""


def _consultar_json(url, params=None):
    try:
        respuesta = requests.get(url, params=params, timeout=TIEMPO_ESPERA)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except (requests.RequestException, TypeError, ValueError) as error:
        raise ErrorServicioExterno from error
    if not isinstance(datos, dict):
        raise ErrorServicioExterno("La respuesta del servicio no tiene un formato válido.")
    return datos


class ServicioClima:
    URL_UBICACION = "https://geocoding-api.open-meteo.com/v1/search"
    URL_CLIMA = "https://api.open-meteo.com/v1/forecast"

    # Códigos WMO que entrega Open-Meteo, traducidos a texto.
    ESTADOS = {
        0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
        45: "Niebla", 48: "Niebla con escarcha",
        51: "Llovizna débil", 53: "Llovizna", 55: "Llovizna intensa",
        61: "Lluvia débil", 63: "Lluvia", 65: "Lluvia intensa",
        66: "Lluvia helada débil", 67: "Lluvia helada",
        71: "Nevada débil", 73: "Nevada", 75: "Nevada intensa", 77: "Granizo fino",
        80: "Chubascos débiles", 81: "Chubascos", 82: "Chubascos violentos",
        85: "Chubascos de nieve", 86: "Chubascos de nieve intensos",
        95: "Tormenta", 96: "Tormenta con granizo", 99: "Tormenta con granizo intenso",
    }

    def buscarUbicacion(self, lugar: str):
        """Busca un lugar de Chile. Devuelve (nombre, región, latitud, longitud) o None."""
        datos = _consultar_json(
            self.URL_UBICACION,
            {"name": lugar, "count": 1, "language": "es", "countryCode": "CL"},
        )
        resultados = datos.get("results")
        if resultados is None:
            return None
        if not isinstance(resultados, list):
            raise ErrorServicioExterno("La lista de ubicaciones recibida no es válida.")
        if not resultados:
            return None
        try:
            if not isinstance(resultados[0], dict):
                raise TypeError
            lugar_encontrado = resultados[0]
            latitud = float(lugar_encontrado["latitude"])
            longitud = float(lugar_encontrado["longitude"])
            if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
                raise ValueError
            return lugar_encontrado["name"], lugar_encontrado.get("admin1", ""), latitud, longitud
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ErrorServicioExterno("La ubicación recibida no es válida.") from error

    def consultarClima(self, latitud: float, longitud: float) -> dict:
        """Devuelve la temperatura (°C), la humedad (%) y el estado del tiempo actuales."""
        datos = _consultar_json(
            self.URL_CLIMA,
            {
                "latitude": latitud, "longitude": longitud,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
                "timezone": "America/Santiago",
            },
        )
        try:
            actual = datos["current"]
            if not isinstance(actual, dict):
                raise TypeError
            temperatura = float(actual["temperature_2m"])
            humedad = int(actual["relative_humidity_2m"])
            codigo = int(actual["weather_code"])
            if (not isfinite(temperatura) or not -90 <= temperatura <= 60
                    or not 0 <= humedad <= 100):
                raise ValueError
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ErrorServicioExterno("Los datos de clima recibidos no son válidos.") from error
        return {
            "temperatura": temperatura,
            "humedad": humedad,
            "estado": self.ESTADOS.get(codigo, "Sin descripción"),
        }


class ServicioCambio:
    URL = "https://mindicador.cl/api/{}"
    MONEDAS = {"USD": ("dolar", "Dólar estadounidense"), "EUR": ("euro", "Euro")}

    def obtenerValor(self, moneda: str):
        """Devuelve (valor en pesos, fecha dd-mm-aaaa) del último registro de la moneda."""
        codigo, _nombre = self.MONEDAS[moneda]
        datos = _consultar_json(self.URL.format(codigo))
        try:
            serie = datos["serie"]
            if not isinstance(serie, list) or not serie or not isinstance(serie[0], dict):
                raise TypeError
            ultimo = serie[0]
            valor = float(ultimo["valor"])
            fecha = datetime.strptime(ultimo["fecha"][:10], "%Y-%m-%d")
            if not isfinite(valor) or valor <= 0:
                raise ValueError
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ErrorServicioExterno("El tipo de cambio recibido no es válido.") from error
        return valor, fecha.strftime("%d-%m-%Y")

    def convertir(self, montoPesos: int, moneda: str):
        """Convierte pesos a la moneda pedida. Devuelve (monto convertido, valor usado, fecha)."""
        valor, fecha = self.obtenerValor(moneda)
        return round(montoPesos / valor, 2), valor, fecha
