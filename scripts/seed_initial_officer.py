from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

def main():
	db = SessionLocal()
	username = "OF01"
	full_name = "NITHISH"
	email = "OF01@example.com"
	contact_number = "9999999999"
	password = "12345"
	existing = db.query(User).filter(User.username == username).first()
	if existing:
		print("Officer already exists.")
		return
	user = User(
		username=username,
		full_name=full_name,
		email=email,
		contact_number=contact_number,
		role=UserRole.OFFICER,
		hashed_password=hash_password(password),
		is_first_login=False,
		is_active=True,
	)
	db.add(user)
	db.commit()
	db.refresh(user)
	print(f"Officer {full_name} created with username {username} and password {password}")
	db.close()

if __name__ == "__main__":
	main()
