# Validación del uso de IA — Viajes Aventura

Herramienta: Claude Code (extensión de VS Code), modelo Claude Opus 5.5.

## 2.1.1 — Implementar el modelo UML en código Python

**Qué se pidió:** pasar el diagrama de clases UML oficial a código Python.

**Resultado:** se crearon las clases (`Usuario`, `Cliente`,
`Administrador`, `Sesion`, `Destino`, `Paquete`, `Reserva` y `Catalogo`). Se mantuvieron los mismos
nombres, atributos privados, métodos y relaciones del UML. Se probó con los datos del caso: el paquete
«Norte Grande» da 516.000 por persona y se rechazan las reservas sin cupo, con 0 personas o con la
fecha de salida vencida.

## 2.1.2 — Aplicar principios de programación orientada a objetos

**Qué se pidió:** revisar el código del 2.1.1 según encapsulamiento, herencia/abstracción y no
duplicación, manteniendo la coherencia con el UML.

**Resultado:** los atributos ya eran privados y solo se acceden con métodos; las listas internas se
entregan como copia. Se eliminó código duplicado en `Cliente`: el RUT y el teléfono ahora usan un
mismo método privado `__enmascarar()`. La herencia `Cliente`/`Administrador` → `Usuario` reutiliza el
login y el hash. `Usuario` se dejó como clase normal (no abstracta) porque así está en el UML.

## Reorganización: `main.py` e `interface.py`

**Qué se pidió:** ordenar el código en dos archivos: `main.py` e `interface.py`.

**Resultado:** las 8 clases del UML quedaron juntas en `main.py`, que también arranca el programa
(`python main.py`). `interface.py` tiene un menú de consola básico: menú principal (ver paquetes,
registrarse, iniciar sesión), menú del administrador (destinos y paquetes) y menú del cliente (reservar
y ver sus reservas). Las contraseñas se piden ocultas y no hay claves escritas en el código: el
administrador se crea al iniciar. Se agregaron 3 métodos de consulta que no están en el UML
(`Paquete.getNombre()`, `Paquete.getFechaSalida()`, `Reserva.getPaquete()`) porque el menú los necesita
para mostrar la información. En esa etapa previa al criterio 2.1.3, los datos se perdían al cerrar el
programa; la siguiente sección documenta la integración de SQLite.

## 2.1.3 — Integrar conexión a base de datos y CRUD

**Qué se pidió:** conectar la solución a una base de datos mediante una librería oficial de Python y
realizar operaciones de creación, consulta, actualización y eliminación.

**Apoyo de IA:** GitHub Copilot en VS Code se utilizó para proponer la capa SQLite, su esquema
relacional y los cambios para conectar el menú y reconstruir el modelo al iniciar. La solución se
revisó contra las clases existentes antes de integrarla.

**Decisiones técnicas revisadas:** se eligió `sqlite3` porque forma parte de la biblioteca estándar y
no requiere instalar ni administrar un servidor. `database.py` define tablas para usuarios, destinos,
paquetes, asociaciones paquete-destino y reservas, con claves foráneas y consultas parametrizadas.
Las contraseñas se guardan como el hash que ya produce `Usuario`, nunca como texto plano. Al cargar,
se conservan los IDs, las asociaciones, los estados de las reservas y el precio fijado al publicar un
paquete. El menú implementa el ciclo de vida de destinos (registro, consulta, actualización del costo y
retiro); las demás entidades también se crean y consultan desde la aplicación y disponen de operaciones
CRUD en la capa de datos.

**Validación ejecutada:** los módulos `main.py`, `interface.py` y `database.py` compilaron con
`py_compile`. Una prueba aislada en una base temporal verificó inserción, consulta, actualización y
eliminación de usuarios, destinos, paquetes y reservas, además del vínculo paquete-destino. Otra prueba
reconstruyó la aplicación desde SQLite y comprobó el inicio de sesión con el hash almacenado, el precio
publicado, el cupo y la reserva; también confirmó que una actualización de costo queda persistida.

**Alcance en esa etapa:** la integración cubría el criterio 2.1.3; en ese momento aún faltaban el
manejo de errores de base de datos y las validaciones del criterio 2.1.4. No se abordó el consumo de
APIs de la Unidad 3.

## 2.1.4 — Manejo de errores y validaciones

**Qué se pidió:** controlar excepciones para proteger la estabilidad del programa y validar los datos
ingresados antes de usarlos.

**Resultado:** en `interface.py` se agregaron validaciones para campos obligatorios, formato de correo,
contraseñas no vacías, enteros dentro de los mínimos permitidos, opciones dentro del rango y fechas
coherentes para los paquetes. Se incorporó manejo de errores SQLite y de acceso al almacenamiento con
mensajes controlados que no exponen detalles internos; la conexión se cierra también si falla el inicio.
Si falla la persistencia de una reserva, destino o paquete, se revierte el cambio en memoria cuando es
posible. Para permitir volver de una opción ingresada por error, los menús principal, cliente y
administrador usan el despachador común `ejecutar_menu()`: muestra una opción de regreso, rechaza
opciones inválidas sin abandonar el menú y permite incorporar futuras opciones agregándolas a su mapa.
El menú de cliente incluye como última opción numerada `4. Cerrar sesión`, que invalida la sesión y
regresa al menú principal; la salida `0` también cierra la sesión. En los formularios se puede escribir
`/volver`; al ingresar una contraseña se puede presionar `Esc`. Cancelar la selección de destinos de un
paquete elimina también el borrador parcial. GitHub Copilot ayudó a identificar y revisar estos
controles.

Se comprobó con `py_compile`, Pylance y pruebas manuales: entradas inválidas se vuelven a solicitar,
errores inducidos no interrumpen el menú ni dejan registros fallidos en memoria, y la navegación permite
volver desde menús y formularios. También se probó una opción futura añadida al mapa común, la
cancelación de contraseña, el cierre de sesión con la opción 4 y el rollback de un paquete parcialmente
creado. Un flujo válido permite crear un paquete, reservar y recargar los datos desde SQLite. El trabajo
se limita al criterio 2.1.4; no incluye consumo de APIs de la Unidad 3.

## Sanitización de entradas

**Qué se pidió:** sanitizar todos los datos que ingresa el usuario.

**Resultado:** en `interface.py` se agregó una sección de sanitización que usan todas las entradas.
Los textos se limpian (se quitan caracteres de control y códigos ANSI que podrían alterar la terminal,
se unen espacios repetidos y se normalizan acentos) y tienen largo máximo. El RUT se valida con su
dígito verificador (módulo 11) y el teléfono con formato de celular chileno; ambos se guardan en un
formato único. El correo se guarda en minúsculas. La contraseña debe tener entre 8 y 64 caracteres.
Los números tienen máximos (costo $50.000.000, duración 60 días, cupo 100, margen 100 %). Se probó con
entradas maliciosas (códigos ANSI, textos de 150 caracteres, números de 20 dígitos, RUT falsos) y
todas fueron rechazadas o limpiadas. Se borró la base de datos de prueba para empezar con datos que
cumplan las nuevas reglas.

## Contraseña con asteriscos y confirmación

**Qué se pidió:** que al escribir la contraseña se vea un `*` por cada carácter y que al crear una
cuenta se deba confirmar.

**Resultado:** `interface.py` lee la contraseña tecla por tecla y muestra un `*` por cada carácter;
permite borrar e ignora flechas y teclas especiales. Funciona en Windows (`msvcrt`) y en Linux/macOS
(`termios`); si la entrada no viene de un teclado, usa `getpass`. Al registrar un cliente o crear el
administrador, la contraseña se pide dos veces y debe coincidir. Al iniciar sesión se pide una sola vez.

## Volver con Esc

**Qué se pidió:** volver al menú anterior con la tecla `Esc` en vez de escribir `/volver`.

**Resultado:** en `interface.py`, la nueva función `leer_linea()` lee lo que se escribe tecla por
tecla (la misma técnica que ya usaba la contraseña) y, si se presiona `Esc`, cancela la acción y
vuelve al menú anterior. La usan todos los formularios (texto, correo, RUT, teléfono, números, fechas
y contraseña) y los menús, que además mantienen su opción `0`. Se quitó `/volver` de los mensajes y
cada pregunta muestra el aviso `(Esc para volver)`. Antes se probó con `0`, pero se descartó
porque obligaba a que el margen no pudiera ser 0 %. Se probó registrar un cliente y volver con `Esc`
al menú principal.

## Confirmación al agregar destinos

**Qué se pidió:** que al elegir un destino para un paquete se avise que quedó agregado.

**Resultado:** en `crear_paquete()` de `interface.py`, al agregar un destino se muestra
`Destino «nombre» agregado (N de 5).` El error que antes era uno solo ahora se separa en dos casos:
destino repetido o paquete con 5 destinos.

## 2.1.5 — Validación crítica del código generado con IA

**Qué se pidió:** revisar el código generado con IA, identificar errores o inconsistencias y
justificar si se adoptó, modificó o descartó, con criterios de seguridad, eficiencia y coherencia.

**Herramientas:** Claude Code (2.1.1, 2.1.2, sanitización, contraseña, navegación y este punto) y
GitHub Copilot (2.1.3 y 2.1.4).

**Adoptado sin cambios:**
- Hash de contraseñas con PBKDF2-SHA256, sal aleatoria y 200.000 iteraciones, y comparación con
  `hmac.compare_digest`. *Seguridad:* la contraseña nunca se guarda en texto plano (R10) y la
  comparación no revela información por el tiempo que tarda.
- Consultas SQL parametrizadas (`?`) en `database.py`. *Seguridad:* evitan la inyección SQL.
- Mensajes de error genéricos ante fallas de SQLite. *Seguridad:* no muestran rutas ni detalles
  internos.

**Modificado:**
- La lectura de la contraseña (`leer_clave`) se generalizó en `leer_linea()`, que ahora usan todas
  las entradas. *Eficiencia:* una sola función en vez de una por tipo de dato.
- El error al agregar destinos ("repetido o ya hay 5") se separó en dos mensajes. *Coherencia:* el
  usuario sabe cuál regla (R3) no cumplió.
- `Usuario` quedó como clase normal, no abstracta, por decisión del equipo. *Coherencia:* así
  está en el UML oficial.

**Descartado:**
- Volver con `1`: es un dato válido (1 persona, 1 día, cupo 1) y la primera opción de los menús.
- Volver con `0`: obligaba a que el margen fuera mínimo 1 %, lo que contradice R6 ("nunca es
  negativo", o sea, 0 % es válido). Se reemplazó por la tecla `Esc`.

**Inconsistencias encontradas al revisar el código contra el caso:**
- R2 y R5/R6 solo se validaban en el menú: las clases `Destino` y `Paquete` aceptaban costo 0 o
  negativo, regreso antes de la salida, cupo 0 y margen negativo. Se agregó la validación en sus
  constructores, como segunda barrera.
- R11: "Mis reservas" revisaba que la sesión estuviera vigente, pero "Reservar" no. Ahora también
  lo revisa.

Se probó cada caso antes y después del cambio: antes se aceptaban costo 0 y negativo, regreso
anterior a la salida, cupo 0, margen −20 % y reservar con una sesión vencida o de otro cliente;
ahora todos se rechazan, los datos válidos se siguen aceptando y la base de datos existente carga
sin errores.

## 3.1.1 — Consumo de servicios externos mediante APIs

**Qué se pidió:** consumir APIs externas con una librería oficial (`requests`), procesar el JSON y
usar solo los datos relevantes, adaptado a Viajes Aventura: clima de un destino y precio de un
paquete en dólares o euros.

**Resultado:** nuevo archivo `servicios_externos.py` con las clases `ServicioClima` (Open-Meteo) y
`ServicioCambio` (mindicador.cl). Del JSON se toman solo la temperatura, la humedad y el código del
tiempo (traducido a texto), y el último valor del dólar o del euro. Antes de usarlos se comprueba que
existan y estén en un rango válido. Se agregaron las opciones al menú del cliente (4 y 5) y al del
administrador (7). Se eligieron APIs sin llave para no tener secretos que guardar.

Al probar con los destinos reales se encontró que el buscador de Open-Meteo solo reconoce ciudades:
"Valle del Elqui", "Cajón del Maipo" o "Salar de Surire" no aparecen. Se descartó guardar
coordenadas en `Destino`, porque obligaba a cambiar el UML y la base de datos. En cambio, si el
destino no se encuentra, el programa pide la ciudad más cercana (por ejemplo, Vicuña). Se probó con
las APIs reales: San Pedro de Atacama, Valle del Elqui con Vicuña, una ciudad inexistente, Norte
Mágico en USD y Gran Chile en EUR. Sin conexión, se muestra un aviso y el programa sigue funcionando.

## 3.1.2 — Mecanismos básicos de seguridad

**Qué se pidió:** inicio de sesión con credenciales encriptadas, validar credenciales y los datos
enviados a la API, controlar datos sensibles y llaves, y que solo usuarios autenticados usen las
funciones.

**Resultado:** el hash PBKDF2 de las contraseñas ya existía. Se agregó:
- Bloqueo de 1 minuto tras 3 intentos fallidos por correo, contado aunque el correo no exista, para
  no revelar cuáles están registrados.
- `cifrado.py`: el RUT y el teléfono se guardan cifrados con Fernet (librería `cryptography`). La
  llave se lee de `.env` con `python-dotenv` y nunca está en el código ni en el repositorio. Si la
  llave no corresponde, se muestra un mensaje genérico, sin la llave ni el detalle del error.
- Validación de la ciudad antes de enviarla a la API (solo letras, espacios, guiones y apóstrofes).
- Las opciones de clima y tipo de cambio revisan que la sesión siga vigente, igual que "Reservar".

Se descartó usar OpenWeatherMap con llave: el cifrado ya obliga a manejar una llave secreta en
`.env`, y además protege los datos sensibles que preocupaban en el caso (Ignacio Salas). Se probó en
una copia: los clientes existentes se cifraron al abrir el programa y se siguen leyendo bien; un
cliente nuevo queda cifrado; con una llave equivocada aparece el mensaje genérico; el cuarto intento
tras 3 fallos queda bloqueado; `<script>`, `12345` y `Vicuña;DROP TABLE` se rechazan como ciudad; y
el clima y el tipo de cambio con una sesión vencida vuelven al menú principal.

## 3.1.3 — Manejo de errores en servicios externos

**Qué se pidió:** aplicar manejo de errores al consumir servicios externos, manteniendo la continuidad
y estabilidad del sistema.

**Revisión del código agregado:** los menús ya controlaban varios errores HTTP y de datos, pero una
respuesta JSON con una estructura inesperada podía producir una excepción no controlada. Se reprodujo
con una respuesta de geolocalización que no era un objeto JSON y se corrigió en la capa de servicios.

**Resultado:** `servicios_externos.py` concentra las consultas HTTP, limita la espera a 10 segundos y
convierte los errores de conexión, HTTP, JSON y formato de respuesta en `ErrorServicioExterno`. Se
validan las coordenadas, los valores de clima y humedad, y el valor, fecha y serie del tipo de cambio.
`interface.py` captura ese error y muestra avisos genéricos para clima y cambio, sin exponer detalles
internos ni cerrar el menú.

**Validación ejecutada:** con respuestas simuladas se comprobó que un timeout, un JSON con tipo
incorrecto, datos de clima con estructura inválida y una serie de tipo de cambio vacía generan el error
controlado. También se verificó que ambas opciones de la interfaz muestran su aviso y regresan sin
propagar la excepción. No se requirió conexión real a las APIs para estas pruebas.

