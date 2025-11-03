# 🧪 Guía de Testing - Farmacruz API

## 📋 Contenido de Tests

La suite de tests completa cubre:

### ✅ Autenticación (8 tests)

* Registro de usuarios
* Login con diferentes roles
* Validación de tokens
* Manejo de errores de autenticación

### ✅ Categorías (9 tests)

* CRUD completo de categorías
* Permisos seller/admin
* Búsqueda de categorías
* Validación de duplicados
* Protección contra eliminación con productos

### ✅ Productos (10 tests)

* CRUD completo de productos
* Actualización de imágenes (seller)
* Gestión de stock
* Búsqueda y filtros
* Permisos por rol

### ✅ Carrito (5 tests)

* Agregar productos al carrito
* Actualizar cantidades
* Proceso de checkout
* Limpieza de carrito

### ✅ Pedidos (6 tests)

* Creación de pedidos
* Actualización de estados
* Filtros por estado
* Permisos por rol

### ✅ Administración (6 tests)

* Dashboard y estadísticas
* Gestión de usuarios
* Permisos administrativos

### ✅ Validación y Errores (6 tests)

* Manejo de tokens inválidos
* Validación de datos
* Recursos inexistentes
* Casos edge

## 🚀 Ejecutar Tests

### Opción 1: Scripts automáticos

**Linux/Mac:**

```bash
chmod +x run_tests.sh
./run_tests.sh
```

**Windows:**

```bash
run_tests.bat
```

### Opción 2: Comando manual

```bash
# Instalar dependencias de test
pip install pytest pytest-cov httpx

# Ejecutar todos los tests
cd backend/farmacruz_api
pytest tests/test_api_complete.py -v

# Con reporte de cobertura
pytest tests/test_api_complete.py -v --cov=. --cov-report=html
```

### Opción 3: Tests específicos

```bash
# Solo tests de autenticación
pytest tests/test_api_complete.py::TestAuth -v

# Solo tests de productos
pytest tests/test_api_complete.py::TestProducts -v

# Solo tests de categorías
pytest tests/test_api_complete.py::TestCategories -v

# Un test específico
pytest tests/test_api_complete.py::TestAuth::test_login_admin -v
```

## 📊 Cobertura de Código

Después de ejecutar los tests con cobertura, abre el reporte HTML:

```bash
# Se genera automáticamente en:
backend/farmacruz_api/htmlcov/index.html

# Abrir en navegador
# Linux/Mac:
open htmlcov/index.html

# Windows:
start htmlcov/index.html
```

## 🎯 Estadísticas Esperadas

Al ejecutar todos los tests deberías ver:

```
✅ Total de tests: ~50
✅ Tests pasados: 50
✅ Cobertura esperada: >85%
⏱️  Tiempo de ejecución: ~10-15 segundos
```

## 📝 Estructura de Tests

```
tests/
├── test_api_complete.py    # Suite completa
├── test_dbf_individual.py  # Tests de DBF
└── test_dbf_traductor.py   # Tests de DBF traductor
```

## 🔍 Debugging Tests

### Ver output detallado:

```bash
pytest tests/test_api_complete.py -v -s
```

### Ver solo tests fallidos:

```bash
pytest tests/test_api_complete.py --lf -v
```

### Parar en el primer error:

```bash
pytest tests/test_api_complete.py -x -v
```

### Ver traceback completo:

```bash
pytest tests/test_api_complete.py -v --tb=long
```

## 🐛 Troubleshooting

### Error: ModuleNotFoundError

```bash
# Asegúrate de estar en el directorio correcto
cd backend/farmacruz_api

# O establece el PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%          # Windows
```

### Error: Database connection

Los tests usan SQLite en memoria, no necesitan PostgreSQL. Si hay error:

```bash
pip install sqlalchemy --upgrade
```

### Error: Token inválido

Los tests crean usuarios de prueba automáticamente. Si fallan:

```bash
# Limpia y vuelve a ejecutar
pytest tests/test_api_complete.py -v --cache-clear
```

## 📈 CI/CD Integration

Para integrar en GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend/farmacruz_api
          pytest tests/test_api_complete.py -v --cov=.
```

## 🎨 Personalizar Tests

### Agregar nuevos tests:

```python
class TestMiNuevaFuncionalidad:
    """Tests de mi nueva funcionalidad"""
  
    def test_mi_caso(self):
        """Descripción del test"""
        response = client.get("/api/v1/mi-endpoint")
        assert response.status_code == 200
```

### Usar fixtures:

```python
@pytest.fixture
def mi_fixture():
    # Setup
    yield data
    # Cleanup
```

## 📞 Soporte

Si tienes problemas con los tests:

1. Verifica que todas las dependencias estén instaladas
2. Revisa que estés en el directorio correcto
3. Limpia el cache de pytest: `pytest --cache-clear`
4. Ejecuta tests individuales para identificar el problema

---

**Última actualización:** Noviembre 2024
**Versión:** 1.0.0
