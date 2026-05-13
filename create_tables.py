"""
Script pour créer toutes les tables de la base de données
"""
from app import app, db
from models import *

def create_all_tables():
    """Crée toutes les tables de la base de données"""
    with app.app_context():
        print("Création de toutes les tables...")
        db.create_all()
        print("✅ Toutes les tables ont été créées avec succès!")
        print("\nTables créées:")
        for table in db.metadata.tables:
            print(f"  - {table}")

if __name__ == '__main__':
    create_all_tables()
















