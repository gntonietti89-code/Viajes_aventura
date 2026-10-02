# Viajes Aventura

Sistema de gestión de destinos, paquetes turísticos y reservas para la agencia Viajes Aventura
(caso 1 · TI3V21 Programación Orientada a Objeto Seguro · INACAP Valparaíso).

El desarrollo sigue, punto por punto, la guía de evaluación de las Unidades 2 y 3 (`seguridad.pdf`),
aplicada al caso de Viajes Aventura (`caso 1 proyecto final.pdf`).

## Avance

| Criterio | Descripción | Estado |
|---|---|---|
| 2.1.1 | Implementar el modelo UML en Python | Hecho |
| 2.1.2 | Principios de POO | Hecho |
| 2.1.3 | Conexión a base de datos (CRUD) | Hecho |
| 2.1.4 | Manejo de errores y validaciones | Hecho |
| 2.1.5 | Validación del código generado con IA | Hecho ([validacion_ia.md](validacion_ia.md)) |
| 3.1.1 | Consumo de servicios externos (APIs) | Hecho |
| 3.1.2 | Mecanismos básicos de seguridad | Hecho |
| 3.1.3 | Manejo de errores en servicios externos | Hecho |

## Estructura

```
Viajes_aventura/
├── main.py            Clases del diagrama UML y punto de partida del programa
├── interface.py       Menú de consola (cliente y administrador)
├── database.py        Conexión SQLite y operaciones CRUD
├── cifrado.py         Cifrado del RUT y el teléfono (Fernet); llave en .env
├── servicios_externos.py  Consumo de APIs: clima (Open-Meteo) y tipo de cambio (mindicador.cl)
├── datos_prueba.py    Carga clientes, destinos, paquetes y reservas de prueba
├── requirements.txt   Librerías externas (requests, cryptography, python-dotenv)
├── uml.png            Diagrama de clases UML oficial
├── validacion_ia.md   Registro del uso de IA
├── caso 1 proyecto final.pdf   Caso Viajes Aventura
├── seguridad.pdf      Guía de evaluación (Unidades 2 y 3)
└── README.md
```

## Cómo ejecutar

```
pip install -r requirements.txt
python main.py
```

En la primera ejecución se crea la cuenta del administrador. Los usuarios, destinos, paquetes y
reservas se guardan en `viajes_aventura.db`, junto al código, y se cargan al iniciar de nuevo el
programa. La base de datos se crea automáticamente y está excluida del control de versiones.

## Persistencia (2.1.3)

`database.py` utiliza `sqlite3`, incluida en Python, con tablas relacionadas para usuarios, destinos,
paquetes, destinos de cada paquete y reservas. La capa de datos ofrece operaciones de creación,
consulta, actualización y eliminación; el menú permite registrar, consultar, actualizar el costo y
retirar destinos, además de registrar usuarios, paquetes y reservas. Las asociaciones y claves
foráneas conservan la relación entre registros. Las contraseñas persistidas siguen siendo hashes,
no texto plano.

## Validaciones y manejo de errores (2.1.4)

El menú valida campos de texto, formato de correo, contraseña no vacía, enteros y rangos permitidos.
También comprueba que la salida de un paquete sea posterior a hoy y que el regreso sea posterior a la
salida, y vuelve a pedir selecciones fuera de rango. Los fallos de SQLite o del almacenamiento se
presentan con mensajes controlados, sin mostrar detalles internos; la conexión se cierra al terminar
o si falla el inicio. Si falla una escritura de reserva o paquete, se evita conservar la operación
fallida en el estado en memoria.

La navegación de los menús principal, cliente y administrador usa el despachador común
`ejecutar_menu()`: `0` regresa al menú anterior o sale, y las opciones inválidas permiten volver a
elegir. En el menú del cliente, la última opción numerada es `6. Cerrar sesión`; al seleccionarla se
cierra la sesión y se regresa al menú principal. En cualquier formulario o menú, la tecla `Esc` cancela la acción y vuelve al menú anterior. Las opciones nuevas se agregan al mapa del
menú y reciben automáticamente el mismo comportamiento. Si se cancela la creación de un paquete, se
elimina también el borrador parcial.

## Sanitización de entradas

Todo dato ingresado pasa por funciones de `interface.py` que limpian caracteres de control y códigos
ANSI, unen espacios repetidos, normalizan acentos y aplican largos máximos. El RUT se valida con su
dígito verificador (sin puntos, ej. 19616711-0) y el teléfono como celular chileno (sin espacios, ej.
+56912345678). La contraseña se escribe con asteriscos y se confirma al crear la cuenta. Límites: contraseña de 8 a 64 caracteres, costo
hasta $50.000.000, duración hasta 60 días, cupo hasta 100 personas y margen hasta 100 %.

Los nombres de clientes, destinos, paquetes y administradores se solicitan con `pedir_nombre()`;
si contienen algún dígito, se rechazan y se vuelven a pedir. Se aceptan nombres con espacios y tildes.

## Servicios externos (3.1.1)

`servicios_externos.py` consume dos APIs públicas con `requests`. Ninguna pide llave de acceso:

- **Clima (Open-Meteo):** `ServicioClima` busca las coordenadas del destino y obtiene la temperatura,
  la humedad y el estado del tiempo actuales. Si el destino no es una ciudad (por ejemplo, Valle del
  Elqui), el programa pide la ciudad más cercana.
- **Tipo de cambio (mindicador.cl, datos del Banco Central):** `ServicioCambio` obtiene el valor del
  dólar y del euro y convierte el precio de un paquete.

Del JSON se toman solo los datos útiles y se comprueba que tengan sentido (que existan y estén en un
rango válido) antes de mostrarlos. Las consultas están en el menú del cliente (opciones 4 y 5) y la de
clima también en el del administrador (opción 7), así que solo se usan después de iniciar sesión.

## Seguridad (3.1.2)

- **Contraseñas:** se guardan como hash PBKDF2-SHA256 con sal, nunca en texto plano (R10).
- **Bloqueo por intentos:** tras 3 intentos fallidos con un mismo correo, ese correo no puede
  iniciar sesión por 1 minuto. Se cuenta igual si el correo no existe, para no revelar cuáles están
  registrados.
- **RUT y teléfono cifrados (R17):** `cifrado.py` los cifra con Fernet antes de guardarlos en
  SQLite y los descifra al cargar. Los clientes guardados antes del cifrado se cifran solos al abrir
  el programa.
- **Llave fuera del código:** la llave de cifrado está en el archivo `.env` (variable
  `VIAJES_CLAVE_CIFRADO`), que está en `.gitignore`. Si no existe, se crea la primera vez. **Si se
  pierde el `.env`, los RUT y teléfonos guardados no se pueden recuperar**, así que hay que
  respaldarlo junto con la base de datos.
- **Validación de datos para la API:** la ciudad solo acepta letras, espacios, guiones y
  apóstrofes (2 a 60 caracteres); la moneda se elige de una lista.
- **Solo usuarios autenticados:** las consultas de clima y tipo de cambio están en los menús con
  sesión iniciada y revisan que la sesión no haya expirado.

## Manejo de errores en servicios externos (3.1.3)

`servicios_externos.py` centraliza las consultas HTTP con un tiempo máximo de espera de 10 segundos,
comprueba errores HTTP y normaliza fallos de conexión, JSON y respuestas con formato inesperado como
`ErrorServicioExterno`. También valida los datos recibidos: coordenadas, valores finitos de clima,
humedad, serie, fecha y tipo de cambio positivo. La interfaz muestra avisos genéricos si falla el
clima o el tipo de cambio y vuelve al menú sin interrumpir el programa.

## Requisitos

- Python 3 (probado con 3.14). Se utiliza la biblioteca estándar, incluida `sqlite3`.
- Librerías de PyPI: `requests` (APIs), `cryptography` (cifrado) y `python-dotenv` (lee `.env`). Se
  instalan con `pip install -r requirements.txt`.
- Conexión a internet para consultar el clima y el tipo de cambio. Sin conexión, el resto del
  programa funciona igual.
