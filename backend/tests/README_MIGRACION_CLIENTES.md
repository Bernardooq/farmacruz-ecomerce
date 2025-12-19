# 🚀 Scripts de Migración de Clientes DBF a FarmaCruz Backend

Este directorio contiene scripts para migrar clientes desde archivos DBF al backend de FarmaCruz.

## 📁 Archivos

### 1. `test_dbf_traductor.py`
Script básico para leer archivos DBF y convertirlos a DataFrames de Pandas.

### 2. `preparar_clientes_csv.py` ⭐ NUEVO
Script para leer el DBF de clientes y generar un CSV limpio y traducido.

**Características:**
- Lee archivos DBF con o sin memo (.fpt)
- Valida columnas requeridas (CVE_CTE, NOM_CTE, etc.)
- Limpia datos (espacios, valores nulos, etc.)
- Genera CSV UTF-8 listo para importar
- Muestra resumen estadístico

### 3. `insertar_clientes.py` ⭐ NUEVO
Script super completo para insertar clientes al backend mediante API REST.

**Características:**
- ✅ Login automático como admin para obtener token JWT
- ✅ Lee CSV/Excel con datos traducidos
- ✅ Inserta cliente por cliente usando los endpoints del backend
- ✅ Crea Customer + CustomerInfo automáticamente
- ✅ Mapeo automático de columnas DBF a campos del backend
- ✅ Manejo de errores robusto
- ✅ Reporte detallado de éxitos/fallos
- ✅ Log de errores en JSON
- ✅ Delay configurable entre peticiones

## 🔄 Flujo de Trabajo Completo

```
DBF de clientes
     ↓
[1] preparar_clientes_csv.py
     ↓
CSV traducido y limpio
     ↓
[2] insertar_clientes.py
     ↓
Backend FarmaCruz (PostgreSQL)
```

## 📋 Requisitos Previos

1. **Backend corriendo:**
   ```bash
   cd backend
   python -m uvicorn farmacruz_api.main:app --reload
   ```

2. **Usuario admin existente** con credenciales conocidas

3. **Dependencias instaladas:**
   ```bash
   pip install pandas dbfread requests
   ```

## 🎯 Uso Paso a Paso

### Paso 1: Preparar CSV desde DBF

1. **Edita `preparar_clientes_csv.py`** y configura:
   ```python
   DBF_PATH = Path(r"C:\ruta\a\tu\CLIENTES.DBF")
   OUTPUT_CSV = Path(r"C:\ruta\salida\clientes_traducido.csv")
   ENCODING = "latin-1"  # o cp850, según tu DBF
   ```

2. **Ejecuta:**
   ```bash
   python preparar_clientes_csv.py
   ```

3. **Verifica el output:**
   - Revisa el CSV generado
   - Verifica el resumen estadístico
   - Confirma que las columnas son correctas

### Paso 2: Insertar al Backend

1. **Asegúrate que el backend está corriendo** en `http://localhost:8000`

2. **Edita `insertar_clientes.py`** y configura:
   ```python
   BACKEND_URL = "http://localhost:8000"
   ADMIN_USERNAME = "admin"
   ADMIN_PASSWORD = "tu_contraseña_admin"  # ⚠️ IMPORTANTE
   DATOS_PATH = Path(r"C:\ruta\a\clientes_traducido.csv")
   ```

3. **Ejecuta:**
   ```bash
   python insertar_clientes.py
   ```

4. **Proceso:**
   - El script hará login automáticamente
   - Mostrará un resumen de los datos a insertar
   - Pedirá confirmación
   - Insertará cliente por cliente
   - Mostrará progreso en tiempo real
   - Generará reporte final

## 📊 Columnas del DBF Mapeadas

El script mapea automáticamente las siguientes columnas del DBF:

### Customer (Tabla Customers)
| DBF         | Backend       | Descripción              |
|-------------|---------------|--------------------------|
| CVE_CTE     | customer_id   | ID del cliente           |
| NOM_CTE     | username      | Username para login      |
| TEL1_CTE    | email (gen.)  | Se genera email único    |
| NOM_CTE     | full_name     | Nombre completo          |
| -           | password      | "FarmaCruz2024!" default |

### CustomerInfo (Tabla CustomerInfo)
| DBF         | Backend        | Descripción                |
|-------------|----------------|----------------------------|
| NOM_FAC     | business_name  | Razón social (o NOM_CTE)   |
| RFC_CTE     | rfc            | RFC del cliente            |
| DIR_CTE     | address_1      | Dirección principal        |
| DIR_ENT     | address_2      | Dirección de entrega       |
| DIR_FAC     | address_3      | Dirección de facturación   |
| -           | sales_group_id | NULL (asignar después)     |
| -           | price_list_id  | NULL (asignar después)     |

## ⚙️ Configuraciones Avanzadas

### Delay entre Peticiones
```python
DELAY = 0.1  # segundos (100ms)
```
- Aumenta si el servidor se sobrecarga
- Reduce para ir más rápido (si el servidor aguanta)

### Encoding del DBF
Encodings comunes para DBF mexicanos:
- `latin-1` (ISO-8859-1)
- `cp850` (DOS Latin 1)
- `cp437` (DOS US)

### Formatos de Entrada Soportados
- ✅ CSV (.csv)
- ✅ Excel (.xlsx, .xls)

## 🐛 Solución de Problemas

### Error: "No se pudo hacer login"
- Verifica que el backend esté corriendo
- Verifica usuario/contraseña
- Confirma que el usuario tiene rol 'admin'

### Error: "La columna 'CVE_CTE' no existe"
- El CSV/Excel debe tener esta columna
- Verifica el encoding del CSV
- Asegúrate de usar el CSV generado por `preparar_clientes_csv.py`

### Error 400: "Usuario ya existe"
- El cliente ya fue insertado
- El script continuará con el siguiente
- Se marcará como "exitoso"

### Muchos errores 500
- Reduce el `DELAY`
- Verifica logs del backend
- Revisa que PostgreSQL esté corriendo

## 📝 Logs y Reportes

Después de ejecutar `insertar_clientes.py`:

1. **Consola:** Muestra progreso en tiempo real
2. **Reporte final:** Estadísticas completas
3. **errores_insercion.json:** Lista de clientes que fallaron

## 🔐 Seguridad

⚠️ **IMPORTANTE:**
- No subas estos scripts con contraseñas hardcodeadas a Git
- Considera usar variables de entorno:
  ```python
  import os
  ADMIN_PASSWORD = os.getenv('FARMACRUZ_ADMIN_PASSWORD', 'default')
  ```

## 📚 Ejemplos

### Ejemplo 1: Inserción Completa
```bash
# 1. Preparar datos
python preparar_clientes_csv.py

# 2. Revisar CSV generado
# (abrir con Excel o editor)

# 3. Insertar
python insertar_clientes.py
```

### Ejemplo 2: Solo Probar con Primeros 10 Clientes
```python
# En insertar_clientes.py, antes de insertar_desde_dataframe():
df = df.head(10)  # Solo primeros 10
```

### Ejemplo 3: Reintentar Solo los Errores
```python
# Si guardaste errores_insercion.json
import json

with open('errores_insercion.json') as f:
    errores = json.load(f)

ids_fallidos = [e['customer_id'] for e in errores if 'customer_id' in e]
df_reintentar = df[df['CVE_CTE'].isin(ids_fallidos)]

# Insertar solo estos
resultado = inserter.insertar_desde_dataframe(df_reintentar)
```

## 🎨 Características Destacadas

### ✨ `preparar_clientes_csv.py`
- 🧹 Limpieza automática de datos
- ✅ Validación de columnas requeridas
- 📊 Resumen estadístico detallado
- 🔍 Preview de primeras filas

### ✨ `insertar_clientes.py`
- 🔐 Login automático con JWT
- 🎯 Inserción transaccional (Customer + CustomerInfo)
- 📈 Progreso en tiempo real
- 🛡️ Manejo robusto de errores
- 📁 Log de errores exportable
- ⏱️ Rate limiting configurable
- 🎨 Output colorido y profesional

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa los logs del backend:**
   ```bash
   # En la terminal donde corre el backend
   # Verás los requests y errores
   ```

2. **Verifica la base de datos:**
   ```sql
   SELECT COUNT(*) FROM customers;
   SELECT COUNT(*) FROM customer_info;
   ```

3. **Prueba manualmente un cliente:**
   ```bash
   curl -X POST http://localhost:8000/customers \
     -H "Authorization: Bearer TU_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"customer_id": 1, "username": "test", "password": "Test123!", "email": "test@test.com"}'
   ```

## 🚀 Próximos Pasos

Después de insertar los clientes:

1. **Asignar Sales Groups:** Cada cliente necesita un `sales_group_id`
2. **Asignar Price Lists:** Cada cliente necesita un `price_list_id`
3. **Actualizar Contraseñas:** Los clientes tienen password por defecto
4. **Validar Datos:** Revisar que RFC, direcciones, etc. sean correctos

## 📄 Licencia

Parte del proyecto FarmaCruz.
