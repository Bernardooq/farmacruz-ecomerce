# Creación de Usuarios Administradores

## 📋 Usuarios Administradores de Farmacruz

Este proyecto incluye 4 usuarios administradores predefinidos:

1. **Israel Saenz** - `israel.saenz@farmacruz.com`
2. **Manuel Saenz** - `manuel.saenz@farmacruz.com`
3. **Andre Saenz** - `andre.saenz@farmacruz.com`
4. **Admin** - `admin@farmacruz.com`

## 🔐 Cómo Asignar Contraseñas y Crear los Usuarios

### Paso 1: Editar el Script

Abre el archivo `create_initial_admins.py` y busca la lista `ADMINS`:

```python
ADMINS = [
    {
        "username": "israel.saenz",
        "email": "israel.saenz@farmacruz.com",
        "full_name": "Israel Saenz",
        "password": ""  # ← ASIGNAR CONTRASEÑA AQUÍ
    },
    {
        "username": "manuel.saenz",
        "email": "manuel.saenz@farmacruz.com",
        "full_name": "Manuel Saenz",
        "password": ""  # ← ASIGNAR CONTRASEÑA AQUÍ
    },
    {
        "username": "andre.saenz",
        "email": "andre.saenz@farmacruz.com",
        "full_name": "Andre Saenz",
        "password": ""  # ← ASIGNAR CONTRASEÑA AQUÍ
    },
    {
        "username": "admin",
        "email": "admin@farmacruz.com",
        "full_name": "Administrador",
        "password": ""  # ← ASIGNAR CONTRASEÑA AQUÍ
    }
]
```

### Paso 2: Asignar las Contraseñas

Reemplaza los campos vacíos con las contraseñas que desees:

```python
ADMINS = [
    {
        "username": "israel.saenz",
        "email": "israel.saenz@farmacruz.com",
        "full_name": "Israel Saenz",
        "password": "ContraseñaSegura123!"  # ← Tu contraseña aquí
    },
    # ... resto de usuarios
]
```

**Requisitos de contraseña:**
- Mínimo 8 caracteres
- Se recomienda usar mayúsculas, minúsculas, números y símbolos

### Paso 3: Ejecutar el Script

```bash
cd backend
python create_initial_admins.py
```

### Paso 4: Verificar

El script mostrará:
- ✅ Usuarios creados exitosamente
- ⚠️ Usuarios que ya existían (omitidos)
- ❌ Errores si los hay

## 🔒 Seguridad

### ⚠️ IMPORTANTE:

1. **NO subas el archivo con contraseñas a Git**
   - Después de asignar las contraseñas, NO hagas commit del archivo
   - O borra las contraseñas del archivo después de ejecutarlo

2. **Las contraseñas se encriptan automáticamente**
   - El script usa bcrypt para hashear las contraseñas
   - Nunca se guardan en texto plano en la base de datos

3. **Comparte las contraseñas de forma segura**
   - Usa un gestor de contraseñas (1Password, LastPass, etc.)
   - O compártelas en persona/llamada
   - NO las envíes por email o chat sin encriptar

4. **Cambio de contraseña en primer login**
   - Pide a cada usuario que cambie su contraseña después del primer login
   - Esto se puede hacer desde el panel de perfil

## 🔄 Alternativas

### Opción 1: Crear Usuarios Uno por Uno (Interactivo)

Si prefieres crear los usuarios de forma interactiva:

```bash
cd backend
python create_admin.py
```

Este script te pedirá los datos de cada usuario.

### Opción 2: Usar Variables de Entorno (Producción)

Para producción, puedes usar:

```bash
export ADMIN_USERNAME=israel.saenz
export ADMIN_EMAIL=israel.saenz@farmacruz.com
export ADMIN_PASSWORD=ContraseñaSegura123!
export ADMIN_FULL_NAME="Israel Saenz"

python init_production.py
```

Repite para cada usuario.

## 📝 Ejemplo Completo

```python
# En create_initial_admins.py
ADMINS = [
    {
        "username": "israel.saenz",
        "email": "israel.saenz@farmacruz.com",
        "full_name": "Israel Saenz",
        "password": "Israel2024Secure!"
    },
    {
        "username": "manuel.saenz",
        "email": "manuel.saenz@farmacruz.com",
        "full_name": "Manuel Saenz",
        "password": "Manuel2024Secure!"
    },
    {
        "username": "andre.saenz",
        "email": "andre.saenz@farmacruz.com",
        "full_name": "Andre Saenz",
        "password": "Andre2024Secure!"
    },
    {
        "username": "admin",
        "email": "admin@farmacruz.com",
        "full_name": "Administrador",
        "password": "Admin2024Secure!"
    }
]
```

Luego ejecuta:
```bash
python create_initial_admins.py
```

Salida esperada:
```
======================================================================
  CREACIÓN DE USUARIOS ADMINISTRADORES - FARMACRUZ
======================================================================

✅ Conexión a la base de datos exitosa

✅ Usuario 'israel.saenz' creado exitosamente
   Email: israel.saenz@farmacruz.com
   Nombre: Israel Saenz
   ID: 1

✅ Usuario 'manuel.saenz' creado exitosamente
   Email: manuel.saenz@farmacruz.com
   Nombre: Manuel Saenz
   ID: 2

✅ Usuario 'andre.saenz' creado exitosamente
   Email: andre.saenz@farmacruz.com
   Nombre: Andre Saenz
   ID: 3

✅ Usuario 'admin' creado exitosamente
   Email: admin@farmacruz.com
   Nombre: Administrador
   ID: 4

======================================================================
  RESUMEN:
  - Usuarios creados: 4
  - Usuarios omitidos (ya existían): 0
======================================================================

✅ Proceso completado exitosamente

⚠️  IMPORTANTE:
   1. Guarda las credenciales en un lugar seguro
   2. Comparte las contraseñas de forma segura con cada usuario
   3. Pídeles que cambien su contraseña en el primer login
```

## 🆘 Troubleshooting

### Error: "Las siguientes cuentas no tienen contraseña asignada"

Asegúrate de haber editado el archivo y asignado contraseñas a todos los usuarios.

### Error: "Las siguientes cuentas tienen contraseñas muy cortas"

Las contraseñas deben tener al menos 8 caracteres.

### Error: "Usuario ya existe"

El usuario ya fue creado anteriormente. El script lo omitirá automáticamente.

### Error de conexión a la base de datos

Verifica que:
1. La base de datos esté corriendo
2. Las variables de entorno estén configuradas correctamente
3. El usuario tenga permisos para crear registros
