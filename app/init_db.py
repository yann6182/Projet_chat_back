from db.database import engine, Base


print("Initialisation de la base de données...")
Base.metadata.create_all(bind=engine)
print(" Tables créées avec succès.")
