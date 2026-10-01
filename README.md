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
| 2.1.3 | Conexión a base de datos (CRUD) | Pendiente |
| 2.1.4 | Manejo de errores y validaciones | Pendiente |
| 2.1.5 | Validación del código generado con IA | En curso ([validacion_ia.md](validacion_ia.md)) |

## Estructura

```
Viajes_aventura/
├── main.py            Clases del diagrama UML y punto de partida del programa
├── interface.py       Menú de consola (cliente y administrador)
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

Al iniciar se crea la cuenta del administrador. Por ahora los datos solo existen mientras el programa
está abierto.

## Requisitos

- Python 3 (probado con 3.14). Por ahora solo se usa la biblioteca estándar.
