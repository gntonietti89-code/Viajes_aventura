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
| 2.1.5 | Validación del código generado con IA | En curso ([validacion_ia.md](validacion_ia.md)) |

## Estructura

```
Viajes_aventura/
├── main.py            Clases del diagrama UML y punto de partida del programa
├── interface.py       Menú de consola (cliente y administrador)
├── database.py        Conexión SQLite y operaciones CRUD
├── uml.png            Diagrama de clases UML oficial
├── validacion_ia.md   Registro del uso de IA
├── caso 1 proyecto final.pdf   Caso Viajes Aventura
├── seguridad.pdf      Guía de evaluación (Unidades 2 y 3)
└── README.md
```

## Cómo ejecutar

```
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
elegir. En el menú del cliente, la última opción numerada es `4. Cerrar sesión`; al seleccionarla se
cierra la sesión y se regresa al menú principal. En cualquier formulario o menú, la tecla `Esc` cancela la acción y vuelve al menú anterior. Las opciones nuevas se agregan al mapa del
menú y reciben automáticamente el mismo comportamiento. Si se cancela la creación de un paquete, se
elimina también el borrador parcial.

## Sanitización de entradas

Todo dato ingresado pasa por funciones de `interface.py` que limpian caracteres de control y códigos
ANSI, unen espacios repetidos, normalizan acentos y aplican largos máximos. El RUT se valida con su
dígito verificador (sin puntos, ej. 19616711-0) y el teléfono como celular chileno (sin espacios, ej.
+56912345678). La contraseña se escribe con asteriscos y se confirma al crear la cuenta. Límites: contraseña de 8 a 64 caracteres, costo
hasta $50.000.000, duración hasta 60 días, cupo hasta 100 personas y margen hasta 100 %.

## Requisitos

- Python 3 (probado con 3.14). Se utiliza la biblioteca estándar, incluida `sqlite3`.
