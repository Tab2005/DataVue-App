from database import SessionLocal, User, UserRole
import sys

def promote_to_superuser(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User {email} not found.")
            return

        print(f"User found: {user.name} ({user.id})")
        print(f"Current Status - Super Admin: {user.is_super_admin}, Role: {user.role}")

        if user.is_super_admin:
            print("User is already a Super Admin.")
        else:
            user.is_super_admin = True
            user.role = UserRole.ADMIN # Also ensure regular admin role
            db.commit()
            print(f"Success! {user.name} has been promoted to Super Admin.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    target_email = "tabchen2005@gmail.com"
    print(f"Promoting {target_email} to Super Admin...")
    promote_to_superuser(target_email)
