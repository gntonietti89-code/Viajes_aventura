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
posible. GitHub Copilot ayudó a identificar los puntos que requerían controles y se revisó el resultado.
Se comprobó con `py_compile`, Pylance y pruebas manuales: entradas inválidas se vuelven a solicitar,
errores inducidos no interrumpen el menú ni dejan reservas o destinos fallidos en memoria, y un flujo
válido permite crear un paquete, reservar y recargar los datos desde SQLite. El trabajo se limita al
criterio 2.1.4; no incluye consumo de APIs de la Unidad 3.
