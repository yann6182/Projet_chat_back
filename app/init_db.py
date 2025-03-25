from db.database import engine, Base

# ✅ Cette ligne importe tous les modèles pour qu’ils soient enregistrés

print("📦 Initialisation de la base de données...")
Base.metadata.create_all(bind=engine)
print("✅ Tables créées avec succès.")
