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
para mostrar la información. Por ahora los datos se pierden al cerrar el programa (la base de datos es
el 2.1.3).
