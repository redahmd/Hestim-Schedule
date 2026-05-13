import sqlite3
import os

path = os.path.join('instance', 'gestion_salles.db')
if os.path.exists(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    print("--- ADMINS ---")
    c.execute("SELECT email FROM utilisateur WHERE role='administrateur' LIMIT 1")
    for r in c.fetchall():
        print(r[0])
    
    print("\n--- ENSEIGNANTS ---")
    c.execute("SELECT email FROM utilisateur WHERE role='enseignant' LIMIT 2")
    for r in c.fetchall():
        print(r[0])
        
    print("\n--- ETUDIANTS ---")
    c.execute("SELECT email FROM utilisateur WHERE role='etudiant' LIMIT 2")
    for r in c.fetchall():
        print(r[0])
    conn.close()
else:
    print("DB not found")
