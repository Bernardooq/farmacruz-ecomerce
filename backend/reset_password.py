"""
Script para resetear o cambiar la contraseña de cualquier usuario.
Uso (desde la carpeta backend): python reset_password.py
"""
import sys
import os
import getpass

# Agregar el directorio farmacruz_api al path para poder importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'farmacruz_api'))

try:
    from sqlalchemy.orm import Session
    from sqlalchemy import text
    from db.session import SessionLocal
    from db.base import User
    from core.security import get_password_hash
    from core.config import DATABASE_URL
except ImportError as e:
    print(f"Error al importar modulos: {e}")
    print("\nAsegurate de:")
    print("1. Estar en la carpeta 'backend'")
    print("2. Tener el entorno virtual activado")
    sys.exit(1)


def reset_user_password():
    print("=" * 60)
    print("  CAMBIO DE CONTRASEÑA DE USUARIO - FARMACRUZ")
    print("=" * 60)
    print()

    # 1. Obtener ID del usuario
    try:
        user_id_str = input("Ingresa el ID del usuario (ej: 1, 15000001, etc): ").strip()
        if not user_id_str:
            print("ID no puede estar vacío.")
            return False
            
        user_id = int(user_id_str)
    except ValueError:
        print("Error: El ID debe ser un número entero válido.")
        return False

    db: Session = SessionLocal()
    
    try:
        # 2. Buscar al usuario
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            print(f"\nError: No se encontró ningún usuario con el ID {user_id}")
            return False
            
        print(f"\nUsuario encontrado:")
        print(f"   Nombre: {user.full_name}")
        print(f"   Username: {user.username}")
        print(f"   Rol: {user.role.value if hasattr(user.role, 'value') else user.role}")
        print(f"   Estado: {'Activo' if user.is_active else 'Inactivo'}\n")
        
        # Confirmar
        confirm = input("¿Es este el usuario al que deseas cambiarle la contraseña? (s/n): ").strip().lower()
        if confirm != 's':
            print("Operación cancelada.")
            return False

        # 3. Pedir contraseñas
        # Usamos getpass para que no se vea lo que escribe en la terminal
        new_password = getpass.getpass("\nIngresa la NUEVA contraseña: ").strip()
        confirm_password = getpass.getpass("Confirma la NUEVA contraseña: ").strip()
        
        if new_password != confirm_password:
            print("\nError: Las contraseñas no coinciden.")
            return False
            
        if len(new_password) < 8:
            print("\nError: La contraseña es muy corta (mínimo 8 caracteres).")
            return False

        # 4. Actualizar en la base de datos
        print("\nEncriptando contraseña y guardando en la base de datos...")
        hashed_password = get_password_hash(new_password)
        
        user.password_hash = hashed_password
        db.commit()
        
        print("¡ÉXITO! La contraseña del usuario '{user.username}' ha sido actualizada correctamente.")
        return True

    except Exception as e:
        print(f"\nError inesperado: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    try:
        reset_user_password()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario.")
        sys.exit(0)

if __name__ == "__main__":
    main()
