# Nombre integrantes
Maximiliano Montoya
Gianni Antonietti

### Nota ### datos adm en el punto 3 


# Guía de instalación y uso del administrador de demostración

Esta guía explica cómo instalar Viajes Aventura en un computador nuevo, cargar los
datos de demostración y entrar con la cuenta de administrador.


##  1. Crear un entorno e instalar las dependencias

Desde la carpeta `Viajes_aventura`, ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Se usa directamente el Python del entorno `.venv`; no hace falta activar el entorno
en PowerShell.

## 2. Cargar los datos para la demostración

Ejecuta este paso antes de iniciar el programa:

```powershell
.\.venv\Scripts\python.exe datos_prueba.py
```

El script crea la base de datos local, el administrador de demostración, clientes,
destinos, paquetes y reservas de ejemplo. Se puede volver a ejecutar: los registros
que ya existen no se duplican.

## 3. Iniciar sesión como administrador

Inicia la aplicación:

```powershell
.\.venv\Scripts\python.exe main.py
```

En el menú principal, selecciona **Iniciar sesión** e ingresa:

| Campo | Valor |
|---|---|
| Correo | `admin@gmail.com` |
| Contraseña | `admin1234` |


## Uso en ejecuciones posteriores

La base de datos se guarda localmente en `viajes_aventura.db`, dentro de la carpeta
del proyecto. Después de cargar los datos por primera vez, para abrir el sistema en
otra ocasión basta con ejecutar:

```powershell
.\.venv\Scripts\python.exe main.py
```

No vuelvas a ejecutar `datos_prueba.py` salvo que quieras volver a cargar los datos
de demostración que falten.


### Aparece `ModuleNotFoundError`

Instala de nuevo las dependencias con el Python del entorno del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Ejecuta también `datos_prueba.py` y `main.py` con
`.\.venv\Scripts\python.exe`, no con otro intérprete de Python.

### No se puede iniciar sesión

- Comprueba que ejecutaste `datos_prueba.py` en la carpeta correcta antes de abrir
  `main.py`.
- Escribe el correo y la contraseña exactamente como aparecen en la tabla.
- Si ya existía una cuenta `admin@gmail.com` en la base de datos local, el cargador
  conserva esa cuenta y no cambia su contraseña. Para una instalación de demostración
  nueva, clona el repositorio en una carpeta nueva y sigue esta guía desde el paso 1.

