from app import app, db
from models import Utilisateur, Professeur
from werkzeug.security import generate_password_hash

def fix_teacher_account():
    with app.app_context():
        print("Verification et correction du compte enseignant...")
        
        # 1. Verifier si l'utilisateur existe
        teacher_email = 'prof@hestim.ma'
        user = Utilisateur.query.filter_by(email=teacher_email).first()
        
        if user:
            print(f"Utilisateur trouve: {user.email}")
            # Reinitialiser le mot de passe
            user.mot_de_passe = generate_password_hash('123456')
            db.session.commit()
            print("Mot de passe reinitialise a: 123456")
        else:
            print("Utilisateur non trouve, creation...")
            user = Utilisateur(
                nom='Bousselham',
                prenom='Mohammed',
                email=teacher_email,
                role='enseignant'
            )
            user.set_password('123456')
            db.session.add(user)
            db.session.commit()
            print("Utilisateur cree avec succes")
        
        # 2. Verifier le profil professeur
        prof = Professeur.query.filter_by(email=teacher_email).first()
        if not prof:
            print("Profil professeur non trouve, creation...")
            prof = Professeur(
                nom='Bousselham',
                prenom='Mohammed',
                email=teacher_email,
                specialite='Informatique',
                departement='Genie Informatique'
            )
            db.session.add(prof)
            db.session.commit()
            print("Profil professeur cree")
        else:
            print(f"Profil professeur existe: {prof.prenom} {prof.nom}")
        
        # 3. Utiliser les comptes enseignants de init_db.py
        print("\n--- Autres comptes enseignants disponibles ---")
        enseignants = Utilisateur.query.filter_by(role='enseignant').limit(5).all()
        for ens in enseignants:
            print(f"Email: {ens.email} | Mot de passe: password123")
        
        print("\n=== Compte enseignant pret ===")
        print(f"Email: {teacher_email}")
        print("Mot de passe: 123456")

if __name__ == '__main__':
    fix_teacher_account()
