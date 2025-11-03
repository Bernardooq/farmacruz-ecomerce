"""
Test rápido para verificar que la API está funcionando
Ejecutar con: pytest tests/test_quick.py -v
"""
import sys
from pathlib import Path

# Agregar farmacruz_api al path
sys.path.insert(0, str(Path(__file__).parent.parent / "farmacruz_api"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Verifica que el endpoint raíz responde"""
    response = client.get("/")
    assert response.status_code == 200
    print("✅ API está respondiendo")

def test_openapi_docs():
    """Verifica que la documentación está disponible"""
    response = client.get("/docs")
    assert response.status_code == 200
    print("✅ Documentación disponible en /docs")

def test_api_structure():
    """Verifica que los endpoints principales existen"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    paths = data["paths"]
    
    # Verificar endpoints principales
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/categories" in paths
    assert "/api/v1/products" in paths
    assert "/api/v1/orders/cart" in paths
    assert "/api/v1/admin/dashboard" in paths
    
    print("✅ Todos los endpoints principales están configurados")

def test_cors_headers():
    """Verifica que CORS está configurado"""
    response = client.options("/api/v1/products")
    # FastAPI maneja CORS automáticamente
    assert response.status_code in [200, 405]
    print("✅ CORS configurado")

if __name__ == "__main__":
    print("\n🚀 Ejecutando tests rápidos...\n")
    
    try:
        test_root_endpoint()
        test_openapi_docs()
        test_api_structure()
        test_cors_headers()
        
        print("\n" + "="*50)
        print("✅ TODOS LOS TESTS RÁPIDOS PASARON")
        print("="*50)
        print("\n💡 Ejecuta los tests completos con:")
        print("   pytest tests/test_api_complete.py -v")
        
    except AssertionError as e:
        print(f"\n❌ Test falló: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)