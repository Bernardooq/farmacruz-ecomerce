"""
Script de PRUEBA RÁPIDA para validar el flujo de inserción
Este script prueba con UN SOLO CLIENTE antes de hacer la inserción masiva
"""

import pandas as pd
import sys
from pathlib import Path

# Importar la clase del script principal
sys.path.insert(0, str(Path(__file__).parent))
from insertar_clientes import FarmaCruzClientInserter


def crear_cliente_prueba() -> pd.DataFrame:
    """
    Crea un DataFrame de prueba con UN cliente
    """
    datos_prueba = {
        'CVE_CTE': [99999],
        'NOM_CTE': ['Cliente Prueba'],
        'DIR_CTE': ['Calle Falsa 123'],
        'COL_CTE': ['Centro'],
        'CD_CTE': ['Ciudad de México'],
        'EDO_CTE': ['CDMX'],
        'RFC_CTE': ['XAXX010101000'],
        'CURP_CTE': [''],
        'CP_CTE': ['01000'],
        'CONTACTO': ['Juan Pérez'],
        'TEL1_CTE': ['5555555555'],
        'TEL2_CTE': [''],
        'TEL3_CTE': [''],
        'FAX_CTE': [''],
        'DESC_CTE': ['0'],
        'LIM_CRE': ['10000'],
        'DIA_CRE': ['30'],
        'FALTA_CTE': [''],
        'PRONTO_P': ['0'],
        'S_FAVOR': ['0'],
        'NOM_FAC': ['CLIENTE PRUEBA SA DE CV'],
        'DIR_FAC': ['Calle Facturación 456'],
        'COL_FAC': ['Roma Norte'],
        'EDO_FAC': ['CDMX'],
        'CD_FAC': ['Ciudad de México'],
        'CVE_AGE': [''],
        'LADA_CTE': ['55'],
        'CVE_ZON': [''],
        'CVE_SUB': [''],
        'CVE_CAN': [''],
        'OBSERVA': ['Cliente de prueba'],
        'COMPRAS': ['0'],
        'PAGOS': ['0'],
        'EXTRA': [''],
        'NOM_ENT': ['Juan Pérez'],
        'DIR_ENT': ['Calle Entrega 789'],
        'COL_ENT': ['Condesa'],
        'CD_ENT': ['Ciudad de México'],
        'EDO_ENT': ['CDMX'],
        'CP_ENT': ['06100'],
        'PROV_CLI': [''],
        'COM_AGE': ['0'],
        'CVE_AGE2': [''],
        'COM_AGE2': ['0'],
        'CUENTA': [''],
        'TXT_ING': [''],
        'OBSERVA2': [''],
        'CHK2DESC': ['0'],
        'LISTA_PREC': ['1']
    }
    
    return pd.DataFrame(datos_prueba)


def main():
    print("=" * 80)
    print("PRUEBA RÁPIDA - INSERCIÓN DE UN SOLO CLIENTE")
    print("=" * 80)
    
    # Configuración
    BACKEND_URL = "http://localhost:8000"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"  # ⚠️ CAMBIAR
    
    # Crear cliente de prueba
    print("\n📋 Cliente de prueba creado:")
    df_prueba = crear_cliente_prueba()
    print(df_prueba[['CVE_CTE', 'NOM_CTE', 'RFC_CTE', 'DIR_CTE']].to_string())
    
    # Crear inserter
    inserter = FarmaCruzClientInserter(base_url=BACKEND_URL)
    
    # Login
    print("\n" + "=" * 80)
    if not inserter.login(ADMIN_USERNAME, ADMIN_PASSWORD):
        print("\n❌ PRUEBA FALLIDA: No se pudo hacer login")
        print("\n🔧 SOLUCIONES:")
        print("   1. Verifica que el backend esté corriendo:")
        print("      cd backend")
        print("      python -m uvicorn farmacruz_api.main:app --reload")
        print("\n   2. Verifica las credenciales en este script")
        print("   3. Verifica que el usuario sea admin")
        return
    
    # Intentar insertar
    print("\n" + "=" * 80)
    print("🧪 Probando inserción del cliente de prueba...")
    print("=" * 80)
    
    resultado = inserter.insertar_desde_dataframe(
        df=df_prueba,
        columna_id='CVE_CTE',
        delay_seconds=0
    )
    
    # Resultado
    print("\n" + "=" * 80)
    if resultado['exitosos'] == 1:
        print("✅ PRUEBA EXITOSA!")
        print("\n🎉 El sistema está listo para la inserción masiva")
        print("\n📋 SIGUIENTE PASO:")
        print("   Ejecuta: python insertar_clientes.py")
    else:
        print("❌ PRUEBA FALLIDA")
        print("\n🔍 DETALLES DEL ERROR:")
        if resultado.get('errores'):
            for error in resultado['errores']:
                print(f"   {error}")
        
        print("\n🔧 POSIBLES SOLUCIONES:")
        print("   1. Revisa los logs del backend")
        print("   2. Verifica que las tablas customers y customer_info existan")
        print("   3. Verifica que el usuario admin tenga permisos")
    
    print("=" * 80)
    
    # Limpieza (opcional)
    if resultado['exitosos'] == 1:
        respuesta = input("\n¿Deseas eliminar el cliente de prueba? (s/n): ").strip().lower()
        if respuesta == 's':
            try:
                import requests
                url = f"{BACKEND_URL}/customers/99999"
                response = requests.delete(url, headers=inserter.headers)
                if response.status_code == 200:
                    print("✅ Cliente de prueba eliminado")
                else:
                    print(f"⚠️  No se pudo eliminar (status {response.status_code})")
            except Exception as e:
                print(f"⚠️  Error eliminando: {e}")


if __name__ == "__main__":
    main()
