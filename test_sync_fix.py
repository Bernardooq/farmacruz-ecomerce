import sys
from pathlib import Path
import json
import gzip
import requests
from datetime import datetime, timezone

# Configurar path para importar config
sys.path.insert(0, str(Path(__file__).parent / "ecommerce" / "servicios"))
from config import BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD
from sync_functions import login

def test_sync():
    print(f"Connecting to {BACKEND_URL}...")
    token = login(BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD)
    if not token:
        print("Login failed")
        return

    # 5 productos de prueba minimalistas (Solo ID, Stock y Fecha)
    test_now = datetime.now(timezone.utc).isoformat()
    productos_test = [
        {"product_id": "COL14", "stock_count": 227, "updated_at": test_now},
        {"product_id": "BRU40", "stock_count": 1, "updated_at": test_now},
        {"product_id": "DEG1", "stock_count": 30, "updated_at": test_now},
        {"product_id": "DEG28", "stock_count": 2, "updated_at": test_now},
        {"product_id": "SON31", "stock_count": 3, "updated_at": test_now}
    ]

    payload = {
        "categorias": ["MED"],
        "productos": productos_test
    }

    # Comprimir payload (Simular cliente real)
    json_data = json.dumps(payload).encode('utf-8')
    compressed = gzip.compress(json_data)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Encoding": "gzip",
        "Content-Type": "application/json"
    }

    print(f"Sending test payload ({len(json_data)/1024:.2f}KB -> {len(compressed)/1024:.2f}KB compressed)...")
    
    endpoint = "/sync-upload/productos-json"
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        response = requests.post(url, data=compressed, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 202:
            print("\n[SUCCESS] Sync accepted by server.")
            print("Wait a few seconds and check 'updated_at' in DB for these 5 products.")
        else:
            print(f"\n[FAILED] Server returned {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sync()
