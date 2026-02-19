"""
Script para crear los 4 usuarios administradores iniciales de Farmacruz
Uso (desde la carpeta backend): python create_initial_admins.py
"""
import sys
import os

# Agregar el directorio farmacruz_api al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'farmacruz_api'))

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    from db.session import SessionLocal
    from db.base import User, UserRole
    from core.security import get_password_hash
    from core.config import DATABASE_URL
except ImportError as e:
    print(f"❌ Error al importar modulos: {e}")
    print("\nAsegurate de:")
    print("1. Estar en la carpeta 'backend'")
    print("2. Tener el entorno virtual activado")
    print("3. Haber instalado las dependencias: pip install -r requirements.txt")
    sys.exit(1)

# Definir los 4 administradores
ADMINS = [
    {
        "user_id": 9001,
        "username": "israel.saenz.admin",
        "email": "israel.saenz.admin@farmacruz.com",
        "full_name": "Israel Saenz",
        "password": "farmasaenz2026"  # Asignar contraseña aqui
    },
    {
        "user_id": 9002,
        "username": "manuel.saenz.admin",
        "email": "manuel.saenz.admin@farmacruz.com",
        "full_name": "Manuel Saenz",
        "password": "farmasaenz2026"  # Asignar contraseña aqui
    },
    {
        "user_id": 9003,
        "username": "andre.saenz.admin",
        "email": "andre.saenz.admin@farmacruz.com",
        "full_name": "Andre Saenz",
        "password": "farmasaenz2026"  # Asignar contraseña aqui
    },
    {
        "user_id": 9004,
        "username": "syncadminssuser2026",
        "email": "admin@farmacruz.com",
        "full_name": "Administrador",
        "password": "ahc4gjnw40blssrtvhjfl4563"  # Asignar contraseña aqui
    },
    {
        "user_id": 9005,
        "username": "ivette.admin",
        "email": "ivette@farmacruz.com",
        "full_name": "Ivette",
        "password": "farmasaenz2026"  # Asignar contraseña aqui
    }
]

def create_admin_users():
    """Crea los 4 usuarios administradores"""
    db: Session = SessionLocal()
    
    print("=" * 70)
    print("  CREACIoN DE USUARIOS ADMINISTRADORES - FARMACRUZ")
    print("=" * 70)
    print()
    
    # Verificar que todas las contraseñas esten asignadas
    missing_passwords = [admin["username"] for admin in ADMINS if not admin["password"]]
    if missing_passwords:
        print("❌ ERROR: Las siguientes cuentas no tienen contraseña asignada:")
        for username in missing_passwords:
            print(f"   - {username}")
        print()
        print("Por favor, edita el archivo 'create_initial_admins.py' y asigna")
        print("las contraseñas en la lista ADMINS antes de ejecutar este script.")
        return False
    
    # Validar longitud de contraseñas
    weak_passwords = [
        admin["username"] for admin in ADMINS 
        if len(admin["password"]) < 8
    ]
    if weak_passwords:
        print("❌ ERROR: Las siguientes cuentas tienen contraseñas muy cortas (minimo 8 caracteres):")
        for username in weak_passwords:
            print(f"   - {username}")
        return False
    
    created_count = 0
    skipped_count = 0
    
    try:
        for admin_data in ADMINS:
            try:
                # Verificar si el usuario ya existe
                existing_user = db.query(User).filter(
                    User.username == admin_data["username"]
                ).first()
                
                if existing_user:
                    print(f"⚠️  Usuario '{admin_data['username']}' ya existe - OMITIDO")
                    skipped_count += 1
                    continue
                
                # Crear el usuario
                hashed_password = get_password_hash(admin_data["password"])
                new_admin = User(
                    user_id=admin_data["user_id"],
                    username=admin_data["username"],
                    email=admin_data["email"],
                    password_hash=hashed_password,
                    full_name=admin_data["full_name"],
                    role=UserRole.admin,
                    is_active=True
                )
                
                db.add(new_admin)
                db.commit()
                db.refresh(new_admin)
                
                print(f"✅ Usuario '{admin_data['username']}' creado exitosamente")
                print(f"   Email: {admin_data['email']}")
                print(f"   Nombre: {admin_data['full_name']}")
                print(f"   ID: {new_admin.user_id}")
                print()
                
                created_count += 1
                
            except Exception as user_error:
                print(f"❌ Error al crear '{admin_data['username']}': {user_error}")
                db.rollback()
                continue
        
        print("=" * 70)
        print(f"  RESUMEN:")
        print(f"  - Usuarios creados: {created_count}")
        print(f"  - Usuarios omitidos (ya existian): {skipped_count}")
        print("=" * 70)
        print()
        
        if created_count > 0:
            print("✅ Proceso completado exitosamente")
            print()
            print("⚠️  IMPORTANTE:")
            print("   1. Guarda las credenciales en un lugar seguro")
            print("   2. Comparte las contraseñas de forma segura con cada usuario")
            print("   3. Pideles que cambien su contraseña en el primer login")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la creacion de usuarios: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_database_connection():
    """Verifica que la conexion a la base de datos funcione"""
    try:
        print(f"🔍 Intentando conectar a la base de datos...")
        print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'configurada'}\n")
        
        db: Session = SessionLocal()
        db.execute(text("SELECT 1"))
        
        # Verificar que la tabla Users existe
        result = db.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        print(f"✅ Conexion exitosa - {count} usuarios existentes en la base de datos\n")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error de conexion a la base de datos:")
        print(f"   {type(e).__name__}: {e}\n")
        print("Verifica que:")
        print("1. PostgreSQL este corriendo (docker-compose up)")
        print("2. Las credenciales en .env sean correctas")
        print("3. La base de datos este inicializada")
        return False

def main():
    # Verificar conexion
    if not verify_database_connection():
        print("Verifica la configuracion de la base de datos y vuelve a intentar.")
        return
    
    # Crear usuarios
    success = create_admin_users()
    
    if not success:
        print("\n❌ El proceso fallo. Revisa los errores anteriores.")
        exit(1)

if __name__ == "__main__":
    main()
