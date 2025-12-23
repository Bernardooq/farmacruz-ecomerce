"""
Script para crear los 4 usuarios administradores iniciales de Farmacruz
Uso: python create_initial_admins.py
"""
from sqlalchemy import text
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.base import User, UserRole
from core.security import get_password_hash

# Definir los 4 administradores
ADMINS = [
    {
        "username": "israel.saenz.admin",
        "email": "israel.saenz.admin@farmacruz.com",
        "full_name": "Israel saenz.admin",
        "password": "farmasaenz123"  # Asignar contraseña aquí
    },
    {
        "username": "manuel.saenz.admin",
        "email": "manuel.saenz.admin@farmacruz.com",
        "full_name": "Manuel saenz.admin",
        "password": "farmasaenz123"  # Asignar contraseña aquí
    },
    {
        "username": "andre.saenz.admin",
        "email": "andre.saenz.admin@farmacruz.com",
        "full_name": "Andre saenz.admin",
        "password": "farmasaenz123"  # Asignar contraseña aquí
    },
    {
        "username": "admin",
        "email": "admin@farmacruz.com",
        "full_name": "Administrador",
        "password": "farmasaenz123"  # Asignar contraseña aquí
    }
]

def create_admin_users():
    """Crea los 4 usuarios administradores"""
    db: Session = SessionLocal()
    
    print("=" * 70)
    print("  CREACIÓN DE USUARIOS ADMINISTRADORES - FARMACRUZ")
    print("=" * 70)
    print()
    
    # Verificar que todas las contraseñas estén asignadas
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
        print("❌ ERROR: Las siguientes cuentas tienen contraseñas muy cortas (mínimo 8 caracteres):")
        for username in weak_passwords:
            print(f"   - {username}")
        return False
    
    created_count = 0
    skipped_count = 0
    
    try:
        for admin_data in ADMINS:
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
        
        print("=" * 70)
        print(f"  RESUMEN:")
        print(f"  - Usuarios creados: {created_count}")
        print(f"  - Usuarios omitidos (ya existían): {skipped_count}")
        print("=" * 70)
        print()
        
        if created_count > 0:
            print("✅ Proceso completado exitosamente")
            print()
            print("⚠️  IMPORTANTE:")
            print("   1. Guarda las credenciales en un lugar seguro")
            print("   2. Comparte las contraseñas de forma segura con cada usuario")
            print("   3. Pídeles que cambien su contraseña en el primer login")
            print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la creación de usuarios: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_database_connection():
    """Verifica que la conexión a la base de datos funcione"""
    try:
        db: Session = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Conexión a la base de datos exitosa\n")
        return True
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}\n")
        return False

def main():
    # Verificar conexión
    if not verify_database_connection():
        print("Verifica la configuración de la base de datos y vuelve a intentar.")
        return
    
    # Crear usuarios
    success = create_admin_users()
    
    if not success:
        print("\n❌ El proceso falló. Revisa los errores anteriores.")
        exit(1)

if __name__ == "__main__":
    main()

