"""Consumo de servicios externos (Unidad 3): clima de un destino y tipo de cambio.

Usa la librería requests (PyPI). Ninguna de las dos APIs pide llave de acceso:
- Open-Meteo (https://open-meteo.com): ubicación y clima actual.
- mindicador.cl: indicadores económicos del Banco Central de Chile (dólar y euro).
"""

import requests

TIEMPO_ESPERA = 10  # segundos; evita que el programa quede esperando a un servicio caído


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
        respuesta = requests.get(
            self.URL_UBICACION,
            params={"name": lugar, "count": 1, "language": "es", "countryCode": "CL"},
            timeout=TIEMPO_ESPERA,
        )
        respuesta.raise_for_status()
        resultados = respuesta.json().get("results")
        if not resultados:
            return None
        lugar_encontrado = resultados[0]
        latitud = float(lugar_encontrado["latitude"])
        longitud = float(lugar_encontrado["longitude"])
        if not (-90 <= latitud <= 90 and -180 <= longitud <= 180):
            raise ValueError("Coordenadas fuera de rango.")
        return lugar_encontrado["name"], lugar_encontrado.get("admin1", ""), latitud, longitud

    def consultarClima(self, latitud: float, longitud: float) -> dict:
        """Devuelve la temperatura (°C), la humedad (%) y el estado del tiempo actuales."""
        respuesta = requests.get(
            self.URL_CLIMA,
            params={
                "latitude": latitud, "longitude": longitud,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
                "timezone": "America/Santiago",
            },
            timeout=TIEMPO_ESPERA,
        )
        respuesta.raise_for_status()
        actual = respuesta.json()["current"]
        # Se toman solo los datos útiles y se comprueba que tengan sentido antes de usarlos.
        temperatura = float(actual["temperature_2m"])
        humedad = int(actual["relative_humidity_2m"])
        codigo = int(actual["weather_code"])
        if not (-90 <= temperatura <= 60 and 0 <= humedad <= 100):
            raise ValueError("Datos de clima fuera de rango.")
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
        respuesta = requests.get(self.URL.format(codigo), timeout=TIEMPO_ESPERA)
        respuesta.raise_for_status()
        ultimo = respuesta.json()["serie"][0]
        valor = float(ultimo["valor"])
        if valor <= 0:
            raise ValueError("Tipo de cambio no válido.")
        anio, mes, dia = ultimo["fecha"][:10].split("-")
        return valor, f"{dia}-{mes}-{anio}"

    def convertir(self, montoPesos: int, moneda: str):
        """Convierte pesos a la moneda pedida. Devuelve (monto convertido, valor usado, fecha)."""
        valor, fecha = self.obtenerValor(moneda)
        return round(montoPesos / valor, 2), valor, fecha
