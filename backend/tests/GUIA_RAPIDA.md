# 🎯 GUÍA RÁPIDA - Migración de Clientes

## ⭐ SCRIPT ÚNICO ALL-IN-ONE

```
backend/tests/
└── 📄 migrar_clientes_dbf.py  ← TODO EN UNO: DBF → Backend directo! 🚀
```

**NO genera archivos intermedios** - Lee el DBF y lo inserta directamente al backend.

---

## 🚀 Uso (¡Solo 2 Pasos!)

### 1️⃣ Configurar el Script

Edita `migrar_clientes_dbf.py` (líneas 20-35):

```python
# Backend URL
BACKEND_URL = "http://localhost:8000"

# Credenciales de Admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # ⚠️ CAMBIAR

# Ruta al archivo DBF
DBF_PATH = Path(r"C:\Users\berna\Downloads\desarrollo\CLIENTES.DBF")

# Encoding del DBF
DBF_ENCODING = "latin-1"

# Delay entre inserciones
DELAY_SECONDS = 0.1

# Modo de prueba (opcional)
TEST_MODE = False  # True para probar solo primeros 5
```

---

### 2️⃣ Ejecutar el Script

```bash
cd backend/tests
python migrar_clientes_dbf.py
```

**¡Y LISTO!** El script hace TODO automáticamente:

1. 🔐 Login como admin
2. 📖 Lee el DBF directamente
3. 🧹 Limpia y valida datos
4. 📊 Muestra resumen
5. ⏳ Pide confirmación
6. 🚀 Inserta cliente por cliente
7. 📈 Muestra progreso en tiempo real
8. ✅ Genera reporte final
9. 📝 Guarda log de errores (si hay)

---

## 🧪 Modo de Prueba

Para probar con solo los primeros 5 clientes:

```python
# En migrar_clientes_dbf.py líneas 34-35
TEST_MODE = True
TEST_LIMIT = 5
```

---

## 📊 Mapeo de Columnas DBF → Backend

| Columna DBF | → | Campo Backend | Tabla |
|-------------|---|---------------|-------|
| `CVE_CTE` | → | `customer_id` | Customer |
| `NOM_CTE` | → | `username`, `full_name` | Customer |
| Auto-generado | → | `email` | Customer |
| `NOM_FAC` | → | `business_name` | CustomerInfo |
| `RFC_CTE` | → | `rfc` | CustomerInfo |
| `DIR_CTE` | → | `address_1` | CustomerInfo |
| `DIR_ENT` | → | `address_2` | CustomerInfo |
| `DIR_FAC` | → | `address_3` | CustomerInfo |

**Notas:**
- Email se genera automáticamente: `{username}@farmacruz.com`
- Password por defecto: `FarmaCruz2024!`
- `sales_group_id` y `price_list_id` se asignan como `null`

---

## 🐛 Troubleshooting

### ❌ Error: "Archivo DBF no encontrado"
```python
# Verifica la ruta en línea 28:
DBF_PATH = Path(r"C:\tu\ruta\CLIENTES.DBF")
```

### ❌ Error: "No se pudo hacer login"
```bash
# 1. ¿Backend corriendo?
cd backend
python -m uvicorn farmacruz_api.main:app --reload

# 2. Verifica credenciales en líneas 23-24
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "tu_contraseña_real"
```

### ❌ Error: "Columna CVE_CTE no existe"
```
El DBF debe tener la estructura correcta de clientes.
Verifica que el archivo sea el correcto.
```

### ⚠️ Muchos errores al insertar
```python
# Reduce el delay (línea 31):
DELAY_SECONDS = 0.2  # Más lento

# O prueba con pocos registros primero:
TEST_MODE = True
TEST_LIMIT = 10
```

---

## 📈 Output del Script

```
================================================================================
  MIGRACIÓN DE CLIENTES DBF → BACKEND FARMACRUZ
================================================================================

📅 Fecha: 2025-12-15 18:51:16
📁 Archivo: CLIENTES.DBF
🔧 Encoding: latin-1
⏱️  Delay: 0.1s

================================================================================

🔐 Haciendo login como admin...
✅ Login exitoso! Token obtenido.

📖 Leyendo CLIENTES.DBF (sin memo)
✅ DBF leído: 1547 registros, 49 columnas

🧹 Limpiando datos...
   Eliminados 3 registros sin CVE_CTE válido
✅ Datos listos: 1544 registros válidos

📊 RESUMEN DE DATOS:
   Registros a procesar: 1544
   Columnas disponibles: 49

🔍 Primeras 3 filas:
   CVE_CTE              NOM_CTE
0        1      FARMACIA CENTRAL
1        2       DROGUERIA LOPEZ
2        3         BOTICA MODERNA

================================================================================

⚠️  ¿Insertar 1544 clientes al backend? (s/n): s

🚀 INICIANDO MIGRACIÓN...

================================================================================

[1/1544] ID: 1 | FARMACIA CENTRAL
      ✅ Insertado exitosamente
[2/1544] ID: 2 | DROGUERIA LOPEZ
      ✅ Insertado exitosamente
...

================================================================================
  REPORTE FINAL DE MIGRACIÓN
================================================================================

⏱️  Duración: 154.32 segundos
📊 Total procesados: 1544
✅ Exitosos: 1542
❌ Fallidos: 2
📈 Tasa de éxito: 99.9%

⚠️  ERRORES (2):
   1. {'customer_id': 999, 'nombre': 'CLIENTE INVALIDO', 'indice': 998}
   2. {'customer_id': 1500, 'nombre': 'ERROR RFC', 'indice': 1499}

📝 Log completo guardado en: C:\...\errores_migracion_20251215_185116.json

================================================================================
✨ MIGRACIÓN COMPLETADA
================================================================================

🎉 ¡Clientes migrados exitosamente!

📋 PRÓXIMOS PASOS:
   1. Asignar sales_group_id a cada cliente
   2. Asignar price_list_id a cada cliente
   3. Enviar instrucciones para cambiar contraseñas
```

---

## ⚡ Características

✅ **Todo en Uno**
- DBF → Backend directo
- Sin archivos intermedios
- Sin pasos manuales

✅ **Robusto**
- Manejo de errores
- Continúa si uno falla
- Valida datos automáticamente

✅ **Informativo**
- Progreso en tiempo real
- Reporte detallado
- Log de errores exportable

✅ **Flexible**
- Modo prueba incluido
- Delay configurable
- Encoding personalizable

---

## 🔐 Seguridad

⚠️ **IMPORTANTE:**
- NO subas el script con contraseñas reales a Git
- Usa variables de entorno en producción:

```python
import os
ADMIN_PASSWORD = os.getenv('FARMACRUZ_ADMIN_PASSWORD', 'default')
```

---

## 📝 Archivos Generados

El script solo genera:
- 📄 Log de errores JSON (si hay errores)
- Ejemplo: `errores_migracion_20251215_185116.json`

---

## 🎯 Próximos Pasos Post-Migración

1. ✅ **Asignar Sales Groups** a cada cliente
2. ✅ **Asignar Price Lists** a cada cliente
3. ✅ **Cambiar Passwords** (se crearon con default)
4. ✅ **Validar Datos** (RFC, direcciones, etc.)

---

## 📞 Endpoints Usados

```
POST   /auth/login              ← Login admin (get token)
POST   /customers               ← Crear customer
PUT    /customers/{id}/info     ← Crear customer_info
```

---

**¡Listo para migrar con UN SOLO COMANDO! 🎉**
