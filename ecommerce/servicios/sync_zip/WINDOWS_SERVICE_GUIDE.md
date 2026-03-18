Configuración de Sincronización Automática en Windows (Task Scheduler)
======================================================================

Para ejecutar los scripts de sincronización automáticamente sin necesidad de que tú los corras, usaremos el **Programador de Tareas de Windows**.

### Requisitos Previos: Configurar Entorno Virtual (Venv)

Como usarás un `venv` específico para servicios, primero debes crearlo e instalar las librerías necesarias.

1.  Abre una terminal (`cmd` o `powershell`) en la carpeta `servicios`:
    ```cmd
    cd C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios
    python -m venv venv
    ```
2.  Actívalo e instala las dependencias:
    ```cmd
    venv\Scripts\activate
    pip install pandas requests dbfread
    ```

### 1. Tarea: Sincronización de Productos (Cada 5 Minutos)

Esta tarea mantendrá actualizados Precios, Existencias y Nuevos Productos.

1.  Abre **Programador de Tareas** (Task Scheduler).
2.  Clic derecho en "Biblioteca del Programador..." -> **Crear Tarea**.
3.  **Pestaña General:**
    *   Nombre: `FarmaCruz_Sync_Products`
    *   Descripción: Sube productos y precios cada 5 min.
    *   Selecciona: "Ejecutar tanto si el usuario inició sesión como si no".
    *   Configurar para: Windows 10.

4.  **Pestaña Desencadenadores (Triggers):**
    *   Nuevo...
    *   Iniciar la tarea: **Al inicio del sistema**.
    *   Repetir tarea cada: **5 minutos**.
    *   Durante: **Indefinidamente**.
    *   Aceptar.

5.  **Pestaña Acciones:**
    *   Nuevo...
    *   Acción: **Iniciar un programa**.
    *   Programa o script: `C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\venv\Scripts\python.exe`
        *   **IMPORTANTE:** Usamos el Python del `venv` de servicios.
    *   Agregar argumentos: `upload_products_sync.py`
    *   Iniciar en (Start in): `C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\sync_zip`

6.  **Pestaña Condiciones:**
    *   Desmarca "Iniciar la tarea solo si el equipo está conectado a corriente AC".

---

### 2. Tarea: Sincronización de Usuarios (Cada 1 Hora)

1.  Crear Nueva Tarea.
2.  **General:** Nombre `FarmaCruz_Sync_Users`.
3.  **Desencadenadores:** Repetir tarea cada **1 hora**.
4.  **Acciones:**
    *   Programa: `C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\venv\Scripts\python.exe`
    *   Argumentos: `upload_users_sync.py`
    *   Iniciar en: `C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\sync_zip`

---

### Verificación

*   En la lista de tareas, da clic derecho a una y selecciona **Ejecutar** para probarla manualmente.
*   Revisa la columna "Resultado de última ejecución". Debe decir `(0x0)` (Éxito).
