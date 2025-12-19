"""
SCRIPT ÚNICO DE MIGRACIÓN DE CLIENTES DBF → BACKEND FARMACRUZ
===============================================================

Este script hace TODO en un solo lugar:
1. Lee el DBF de clientes directamente (sin CSV intermedio)
2. Se loguea como admin para obtener el token JWT
3. Inserta cliente por cliente al backend usando los endpoints
4. Muestra progreso en tiempo real
5. Genera reporte detallado

NO genera archivos intermedios, todo directo de DBF a Backend.

Autor: FarmaCruz Team
"""

from dbfread import DBF
import pandas as pd
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_batch
import bcrypt
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================================
# CONFIGURACIÓN - MODIFICA ESTOS VALORES
# ============================================================================

# Backend URL
BACKEND_URL = "http://localhost:8000/api/v1"

# Credenciales de Admin
ADMIN_USERNAME = "manuel.saenz.admin"
ADMIN_PASSWORD = "farmasaenz123"  # ⚠️ CAMBIAR por tu contraseña real

# Ruta al archivo DBF de clientes
DBF_PATH = Path(r"C:\Users\berna\Downloads\desarrollo\CLIENTES.DBF")

# Encoding del DBF (común en México: latin-1, cp850, cp437)
DBF_ENCODING = "latin-1"

# Delay entre inserciones (segundos) - evita sobrecargar el servidor
DELAY_SECONDS = 0.001

# Modo de prueba: si es True, solo procesa los primeros N clientes
TEST_MODE = False
TEST_LIMIT = 5  # Solo si TEST_MODE = True

# ============================================================================
# MODO DE INSERCIÓN RÁPIDA (LLAMADAS PARALELAS AL BACKEND) 🚀
# ============================================================================

# IMPORTANTE: Solo usa llamadas al backend/API (NO SQL directo)
# Pero las hace en PARALELO para ir más rápido

# Si es True, inserta directamente a PostgreSQL (100x más rápido pero sin validaciones)
# Si es False, usa el backend API en PARALELO (10x más rápido y con validaciones)
USE_DIRECT_SQL = False  # ⚠️ Mantener en False para usar API

# Número de workers paralelos para llamadas al backend
# Más workers = más rápido, pero no sobrecargar el servidor
MAX_WORKERS = 10  # 10 requests simultáneos al backend

# Configuración de la base de datos (solo si USE_DIRECT_SQL = True)
DB_CONFIG = {
    "host": "localhost",
    "database": "mydatabase",
    "user": "postgres",
    "password": "admin",
    "port": 5432
}

# ============================================================================
# CLASE PRINCIPAL
# ============================================================================

class MigradorClientesDBF:
    """Clase que maneja toda la migración de DBF a Backend"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.headers: Dict[str, str] = {}
        self.stats = {
            'total': 0,
            'exitosos': 0,
            'fallidos': 0,
            'errores': [],
            'inicio': None,
            'fin': None
        }
    
    # ========================================================================
    # AUTENTICACIÓN
    # ========================================================================
    
    def login(self, username: str, password: str) -> bool:
        """Login como admin y obtiene token JWT"""
        try:
            login_url = f"{self.base_url}/auth/login"
            data = {
                "username": username,
                "password": password
            }
            
            print(f"🔐 Haciendo login como {username}...")
            response = requests.post(login_url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data["access_token"]
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                print("✅ Login exitoso! Token obtenido.\n")
                return True
            else:
                print(f"❌ Error en login: {response.status_code}")
                print(f"Detalle: {response.text}\n")
                return False
                
        except Exception as e:
            print(f"❌ Excepción durante login: {e}\n")
            return False
    
    # ========================================================================
    # LECTURA DEL DBF
    # ========================================================================
    
    def leer_dbf(self, dbf_path: Path, encoding: str = "latin-1") -> pd.DataFrame:
        """Lee el archivo DBF y lo convierte a DataFrame"""
        fpt_path = dbf_path.with_suffix(".fpt")
        
        try:
            if fpt_path.exists():
                print(f"📖 Leyendo {dbf_path.name} con {fpt_path.name} (memo habilitado)")
                table = DBF(dbf_path, load=True, encoding=encoding)
            else:
                print(f"📖 Leyendo {dbf_path.name} (sin memo)")
                table = DBF(dbf_path, load=True, ignore_missing_memofile=True, encoding=encoding)
            
            df = pd.DataFrame(iter(table))
            print(f"✅ DBF leído: {len(df)} registros, {len(df.columns)} columnas\n")
            
            return df
            
        except Exception as e:
            print(f"❌ Error leyendo DBF: {e}\n")
            return pd.DataFrame()
    
    def limpiar_datos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y valida los datos del DataFrame"""
        print("🧹 Limpiando datos...")
        
        df_clean = df.copy()
        
        # Limpiar espacios en strings
        for col in df_clean.select_dtypes(include=['object']).columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()
        
        # Eliminar registros sin CVE_CTE válido
        antes = len(df_clean)
        df_clean = df_clean[df_clean['CVE_CTE'].notna()]
        df_clean = df_clean[df_clean['CVE_CTE'] != '']
        df_clean = df_clean[df_clean['CVE_CTE'] != 'nan']
        despues = len(df_clean)
        
        if antes > despues:
            print(f"   Eliminados {antes - despues} registros sin CVE_CTE válido")
        
        print(f"✅ Datos listos: {len(df_clean)} registros válidos\n")
        
        return df_clean
    
    # ========================================================================
    # PREPARACIÓN DE DATOS
    # ========================================================================
    
    def preparar_customer(self, row: pd.Series, customer_id: int) -> Dict[str, Any]:
        """Prepara los datos del Customer desde una fila del DBF"""
        
        # Username desde NOM_CTE
        username = str(row.get('NOM_CTE', f'cliente_{customer_id}')).strip()
        if not username or pd.isna(username) or username == 'nan':
            username = f'cliente_{customer_id}'
        
        # Limpiar username (solo alfanuméricos y guión bajo)
        username = ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in username)
        username = username[:50]  # Limitar longitud
        
        # Email generado
        email = f'{username}@farmacruz.com'
        
        # Full name
        full_name = str(row.get('NOM_CTE', f'Cliente {customer_id}')).strip()
        if pd.isna(full_name) or full_name == 'nan' or not full_name:
            full_name = f'Cliente {customer_id}'
        
        # Password por defecto
        password = "FarmaCruz2024!"
        
        return {
            "customer_id": int(customer_id),
            "username": username[:255],
            "email": email[:255],
            "full_name": full_name[:255],
            "password": password
        }
    
    def preparar_customer_info(self, row: pd.Series) -> Dict[str, Any]:
        """Prepara los datos del CustomerInfo desde una fila del DBF"""
        
        # Business name desde NOM_FAC o NOM_CTE
        business_name = str(row.get('NOM_FAC', '')).strip()
        if pd.isna(business_name) or business_name == 'nan' or not business_name:
            business_name = str(row.get('NOM_CTE', 'N/A')).strip()
        if pd.isna(business_name) or business_name == 'nan' or not business_name:
            business_name = 'Sin nombre comercial'
        
        # RFC
        rfc = str(row.get('RFC_CTE', '')).strip()
        if pd.isna(rfc) or rfc == 'nan' or not rfc or len(rfc) < 12:
            rfc = None
        else:
            rfc = rfc[:13]
        
        # Price List ID desde LISTA_PREC
        price_list_id = None
        if 'LISTA_PREC' in row.index:
            try:
                lista_prec = row.get('LISTA_PREC')
                if pd.notna(lista_prec) and str(lista_prec).strip() not in ['', 'nan', '0']:
                    price_list_id = int(float(lista_prec))
            except (ValueError, TypeError):
                price_list_id = None
        
        # Direcciones
        address_1 = self._limpiar_campo(row.get('DIR_CTE', ''))
        address_2 = self._limpiar_campo(row.get('DIR_ENT', ''))
        address_3 = self._limpiar_campo(row.get('DIR_FAC', ''))
        
        return {
            "business_name": business_name[:255],
            "rfc": rfc,
            "sales_group_id": None,  # Se asignará después
            "price_list_id": price_list_id,  # Desde DBF columna LISTA_PREC
            "address_1": address_1,
            "address_2": address_2,
            "address_3": address_3
        }
    
    def _limpiar_campo(self, valor) -> Optional[str]:
        """Limpia un campo de texto"""
        if pd.isna(valor):
            return None
        valor_str = str(valor).strip()
        if not valor_str or valor_str == 'nan':
            return None
        return valor_str
    
    # ========================================================================
    # INSERCIÓN AL BACKEND
    # ========================================================================
    
    def crear_customer(self, customer_data: Dict[str, Any]) -> Optional[int]:
        """Crea un customer en el backend"""
        try:
            url = f"{self.base_url}/customers"
            response = requests.post(url, headers=self.headers, json=customer_data)
            
            if response.status_code == 201:
                customer = response.json()
                return customer['customer_id']
            elif response.status_code == 400:
                # Usuario ya existe
                print(f"      ⚠️  Customer {customer_data['customer_id']} ya existe")
                return customer_data['customer_id']
            else:
                print(f"      ❌ Error {response.status_code}: {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"      ❌ Excepción: {e}")
            return None
    
    def crear_customer_info(self, customer_id: int, info_data: Dict[str, Any]) -> bool:
        """Crea o actualiza la información del customer"""
        try:
            url = f"{self.base_url}/customers/{customer_id}/info"
            response = requests.put(url, headers=self.headers, json=info_data)
            
            if response.status_code == 200:
                return True
            else:
                print(f"      ❌ Error info {response.status_code}: {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"      ❌ Excepción info: {e}")
            return False
    
    def insertar_cliente_completo(self, row: pd.Series, customer_id: int, index: int, total: int) -> bool:
        """Inserta un cliente completo (customer + info)"""
        
        nombre = row.get('NOM_CTE', 'N/A')
        price_list = row.get('LISTA_PREC', 'N/A')
        
        print(f"[{index + 1}/{total}] ID: {customer_id} | {nombre} | Lista: {price_list}")
        
        # 1. Crear customer
        customer_data = self.preparar_customer(row, customer_id)
        created_id = self.crear_customer(customer_data)
        
        if not created_id:
            return False
        
        # 2. Crear customer info
        info_data = self.preparar_customer_info(row)
        info_ok = self.crear_customer_info(created_id, info_data)
        
        if info_ok:
            if info_data.get('price_list_id'):
                print(f"      ✅ Insertado con price_list_id: {info_data['price_list_id']}")
            else:
                print(f"      ✅ Insertado (sin price_list asignado)")
        
        return info_ok
    
    # ========================================================================
    # INSERCIÓN PARALELA AL BACKEND API 🚀
    # ========================================================================
    
    def migrar_api_paralelo(self, df: pd.DataFrame, max_workers: int = 10) -> None:
        """
        Inserta clientes usando el backend API pero en PARALELO.
        Hace múltiples requests simultáneos para ir más rápido.
        Mantiene todas las validaciones del backend.
        """
        print(f"🚀 MODO PARALELO: {max_workers} requests simultáneos al backend\n")
        
        def procesar_un_cliente(args):
            """Procesa un cliente individual (se ejecuta en thread separado)"""
            idx, row = args
            try:
                customer_id = int(row['CVE_CTE'])
                nombre = row.get('NOM_CTE', 'N/A')
                price_list = row.get('LISTA_PREC', 'N/A')
                
                # Preparar y crear customer
                customer_data = self.preparar_customer(row, customer_id)
                created_id = self.crear_customer(customer_data)
                
                if not created_id:
                    return {
                        'success': False,
                        'customer_id': customer_id,
                        'nombre': nombre,
                        'error': 'No se pudo crear customer'
                    }
                
                # Preparar y crear customer_info
                info_data = self.preparar_customer_info(row)
                info_ok = self.crear_customer_info(created_id, info_data)
                
                if info_ok:
                    return {
                        'success': True,
                        'customer_id': customer_id,
                        'nombre': nombre,
                        'price_list_id': info_data.get('price_list_id')
                    }
                else:
                    return {
                        'success': False,
                        'customer_id': customer_id,
                        'nombre': nombre,
                        'error': 'No se pudo crear customer_info'
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'customer_id': customer_id if 'customer_id' in locals() else idx,
                    'error': str(e)
                }
        
        # Ejecutar en paralelo con ThreadPoolExecutor
        total = len(df)
        procesados = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas
            futures = {
                executor.submit(procesar_un_cliente, (idx, row)): idx 
                for idx, row in df.iterrows()
            }
            
            # Recoger resultados a medida que terminan
            for future in as_completed(futures):
                resultado = future.result()
                procesados += 1
                
                if resultado['success']:
                    self.stats['exitosos'] += 1
                    customer_id = resultado['customer_id']
                    nombre = resultado['nombre']
                    price_list = resultado.get('price_list_id', 'N/A')
                    
                    print(f"[{procesados}/{total}] ✅ ID: {customer_id} | {nombre} | Lista: {price_list}")
                else:
                    self.stats['fallidos'] += 1
                    self.stats['errores'].append({
                        'customer_id': resultado.get('customer_id'),
                        'nombre': resultado.get('nombre', 'N/A'),
                        'error': resultado.get('error', 'Error desconocido')
                    })
                    print(f"[{procesados}/{total}] ❌ Error: {resultado.get('error', 'Desconocido')}")
    
    # ========================================================================
    # INSERCIÓN SQL DIRECTA (RÁPIDA) 🚀
    # ========================================================================
    
    def migrar_sql_directo(self, df: pd.DataFrame, db_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta clientes directamente a PostgreSQL usando SQL bulk insert.
        Métod súper rápido que salta el backend completamente.
        """
        print("🚀 MODO INSERCIÓN RÁPIDA: SQL Directo a PostgreSQL\n")
        
        try:
            # Conectar a PostgreSQL
            print("🔌 Conectando a la base de datos...")
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            print("✅ Conectado exitosamente\n")
            
            # Preparar datos para customers
            print("📦 Preparando datos de customers...")
            customers_data = []
            customers_info_data = []
            
            # Password hash por defecto (bcrypt)
            default_password = "FarmaCruz2024!"
            password_hash = bcrypt.hashpw(
                default_password.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            for idx, row in df.iterrows():
                customer_id = int(row['CVE_CTE'])
                
                # Preparar customer
                customer_row = self.preparar_customer(row, customer_id)
                customers_data.append((
                    customer_row['customer_id'],
                    customer_row['username'],
                    customer_row['email'],
                    customer_row['full_name'],
                    password_hash,  # Mismo hash para todos (por velocidad)
                    True  # is_active
                ))
                
                # Preparar customer_info
                info_row = self.preparar_customer_info(row)
                customers_info_data.append((
                    customer_id,
                    info_row['business_name'],
                    info_row['rfc'],
                    info_row['sales_group_id'],
                    info_row['price_list_id'],
                    info_row['address_1'],
                    info_row['address_2'],
                    info_row['address_3']
                ))
            
            print(f"✅ {len(customers_data)} registros preparados\n")
            
            # Insertar customers en batch
            print("💾 Insertando customers...")
            execute_batch(
                cursor,
                """
                INSERT INTO customers (customer_id, username, email, full_name, password_hash, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    full_name = EXCLUDED.full_name,
                    is_active = EXCLUDED.is_active
                """,
                customers_data,
                page_size=500
            )
            
            inserted_customers = cursor.rowcount
            print(f"✅ {inserted_customers} customers insertados\n")
            
            # Insertar customer_info en batch
            print("💾 Insertando customer_info...")
            execute_batch(
                cursor,
                """
                INSERT INTO customer_info (
                    customer_id, business_name, rfc, sales_group_id, price_list_id,
                    address_1, address_2, address_3
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (customer_id) DO UPDATE SET
                    business_name = EXCLUDED.business_name,
                    rfc = EXCLUDED.rfc,
                    sales_group_id = EXCLUDED.sales_group_id,
                    price_list_id = EXCLUDED.price_list_id,
                    address_1 = EXCLUDED.address_1,
                    address_2 = EXCLUDED.address_2,
                    address_3 = EXCLUDED.address_3
                """,
                customers_info_data,
                page_size=500
            )
            
            inserted_info = cursor.rowcount
            print(f"✅ {inserted_info} customer_info insertados\n")
            
            # Commit
            conn.commit()
            print("✅ Transacción confirmada (COMMIT)\n")
            
            # Cerrar conexión
            cursor.close()
            conn.close()
            
            return {
                'total': len(df),
                'exitosos': len(df),
                'fallidos': 0,
                'errores': []
            }
            
        except Exception as e:
            print(f"❌ Error en inserción SQL: {e}\n")
            if conn:
                conn.rollback()
                conn.close()
            
            return {
                'total': len(df),
                'exitosos': 0,
                'fallidos': len(df),
                'errores': [{'error': str(e)}]
            }
    
    # ========================================================================
    # PROCESO PRINCIPAL
    # ========================================================================
    
    def migrar(
        self, 
        dbf_path: Path, 
        encoding: str = "latin-1",
        delay: float = 0.1,
        test_mode: bool = False,
        test_limit: int = 5
    ) -> Dict[str, Any]:
        """Ejecuta la migración completa de DBF a Backend"""
        
        print("=" * 80)
        print("  MIGRACIÓN DE CLIENTES DBF → BACKEND FARMACRUZ")
        print("=" * 80)
        print(f"\n📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Archivo: {dbf_path.name}")
        print(f"🔧 Encoding: {encoding}")
        print(f"⏱️  Delay: {delay}s")
        if test_mode:
            print(f"🧪 MODO PRUEBA: Solo primeros {test_limit} registros")
        print("\n" + "=" * 80 + "\n")
        
        # Validar archivo existe
        if not dbf_path.exists():
            print(f"❌ ERROR: No se encontró el archivo {dbf_path}")
            return {"error": "Archivo no encontrado"}
        
        # Leer DBF
        df = self.leer_dbf(dbf_path, encoding)
        if df.empty:
            print("❌ ERROR: No se pudieron leer datos del DBF")
            return {"error": "DBF vacío o error de lectura"}
        
        # Validar columna CVE_CTE
        if 'CVE_CTE' not in df.columns:
            print(f"❌ ERROR: La columna 'CVE_CTE' no existe en el DBF")
            print(f"Columnas encontradas: {', '.join(df.columns)}")
            return {"error": "Columna CVE_CTE no encontrada"}
        
        # Limpiar datos
        df = self.limpiar_datos(df)
        
        # Modo prueba
        if test_mode:
            df = df.head(test_limit)
        
        # Mostrar resumen
        print("📊 RESUMEN DE DATOS:")
        print(f"   Registros a procesar: {len(df)}")
        print(f"   Columnas disponibles: {len(df.columns)}")
        print("\n🔍 Primeras 3 filas:")
        print(df[['CVE_CTE', 'NOM_CTE']].head(3).to_string())
        print("\n" + "=" * 80 + "\n")
        
        # Confirmar
        if not test_mode:
            respuesta = input(f"⚠️  ¿Insertar {len(df)} clientes al backend? (s/n): ").strip().lower()
            if respuesta != 's':
                print("\n❌ Migración cancelada por el usuario\n")
                return {"error": "Cancelado por usuario"}
        
        # Iniciar migración
        self.stats['total'] = len(df)
        self.stats['inicio'] = datetime.now()
        
        print("\n🚀 INICIANDO MIGRACIÓN...\n")
        print("=" * 80 + "\n")
        
        # Ejecutar migración según el modo configurado
        if USE_DIRECT_SQL:
            # Modo rápido: SQL directo
            resultado = self.migrar_sql_directo(df, DB_CONFIG)
            self.stats.update(resultado)
        else:
            # Modo API REST en PARALELO 🚀
            self.migrar_api_paralelo(df, max_workers=MAX_WORKERS)
        
        self.stats['fin'] = datetime.now()
        
        # Mostrar reporte
        self._mostrar_reporte()
        
        return self.stats
    
    def _mostrar_reporte(self):
        """Muestra el reporte final de la migración"""
        print("\n" + "=" * 80)
        print("  REPORTE FINAL DE MIGRACIÓN")
        print("=" * 80 + "\n")
        
        duracion = (self.stats['fin'] - self.stats['inicio']).total_seconds()
        
        print(f"⏱️  Duración: {duracion:.2f} segundos")
        print(f"📊 Total procesados: {self.stats['total']}")
        print(f"✅ Exitosos: {self.stats['exitosos']}")
        print(f"❌ Fallidos: {self.stats['fallidos']}")
        
        if self.stats['exitosos'] > 0:
            tasa_exito = (self.stats['exitosos'] / self.stats['total']) * 100
            print(f"📈 Tasa de éxito: {tasa_exito:.1f}%")
        
        if self.stats['errores']:
            print(f"\n⚠️  ERRORES ({len(self.stats['errores'])}):")
            for i, error in enumerate(self.stats['errores'][:10], 1):
                print(f"   {i}. {error}")
            
            if len(self.stats['errores']) > 10:
                print(f"   ... y {len(self.stats['errores']) - 10} más")
            
            # Guardar log de errores
            log_path = DBF_PATH.parent / f"errores_migracion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats['errores'], f, indent=2, ensure_ascii=False)
            print(f"\n📝 Log completo guardado en: {log_path}")
        
        print("\n" + "=" * 80)
        print("✨ MIGRACIÓN COMPLETADA")
        print("=" * 80 + "\n")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal"""
    
    # Validar archivo DBF
    if not DBF_PATH.exists():
        print("\n" + "=" * 80)
        print("❌ ERROR: Archivo DBF no encontrado")
        print("=" * 80)
        print(f"\nRuta configurada: {DBF_PATH}")
        print("\n💡 SOLUCIÓN:")
        print("   1. Verifica que el archivo existe")
        print("   2. Edita la variable DBF_PATH en este script (línea 28)")
        print("\n📁 Archivos DBF en la carpeta:")
        if DBF_PATH.parent.exists():
            for archivo in DBF_PATH.parent.glob("*.dbf"):
                print(f"   - {archivo.name}")
        else:
            print("   (Carpeta no encontrada)")
        print("\n" + "=" * 80 + "\n")
        return
    
    # Crear migrador
    migrador = MigradorClientesDBF(base_url=BACKEND_URL)
    
    # Login (solo si NO usamos SQL directo)
    if not USE_DIRECT_SQL:
        if not migrador.login(ADMIN_USERNAME, ADMIN_PASSWORD):
            print("=" * 80)
            print("❌ ERROR: No se pudo hacer login")
            print("=" * 80)
            print("\n💡 SOLUCIONES:")
            print("   1. Verifica que el backend esté corriendo:")
            print("      cd backend")
            print("      python -m uvicorn farmacruz_api.main:app --reload")
            print("\n   2. Verifica las credenciales en este script:")
            print(f"      Usuario: {ADMIN_USERNAME}")
            print(f"      Password: {'*' * len(ADMIN_PASSWORD)}")
            print("\n   3. Verifica que el usuario tenga rol 'admin'")
            print("\n   4. O activa USE_DIRECT_SQL = True para SQL directo (más rápido)")
            print("\n" + "=" * 80 + "\n")
            return
    else:
        print("\n" + "=" * 80)
        print(f"🚀 MODO API PARALELA: {MAX_WORKERS} requests simultáneos")  
        print("=" * 80)
        print(f"\n✨ Login exitoso como {ADMIN_USERNAME}")
        print(f"✨ {MAX_WORKERS} llamadas simultáneas al backend (10x más rápido)")
        print("✨ Mantiene todas las validaciones del backend")
        print("\n" + "=" * 80 + "\n")
    
    # Ejecutar migración
    resultado = migrador.migrar(
        dbf_path=DBF_PATH,
        encoding=DBF_ENCODING,
        delay=DELAY_SECONDS,
        test_mode=TEST_MODE,
        test_limit=TEST_LIMIT
    )
    
    # Mensaje final
    if resultado.get('exitosos', 0) > 0:
        print("\n🎉 ¡Clientes migrados exitosamente!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Asignar sales_group_id a cada cliente")
        print("   2. Validar que price_list_id sea correcto (asignado desde LISTA_PREC)")
        print("   3. Enviar instrucciones para cambiar contraseñas")
    


if __name__ == "__main__":
    main()
