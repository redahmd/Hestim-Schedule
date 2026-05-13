from app import app
from database import db
from models import Etudiant, Utilisateur
from routes.reservations import envoyer_email_notification

def run_task():
    with app.app_context():
        email = "redahmd721@gmail.com"
        
        # Check if user exists
        etudiant = Etudiant.query.filter_by(email=email).first()
        if not etudiant:
            etudiant = Etudiant(nom="Ahmed", prenom="Reda", email=email, niveau="M1", actif=True)
            db.session.add(etudiant)
            
        utilisateur = Utilisateur.query.filter_by(email=email).first()
        if not utilisateur:
            utilisateur = Utilisateur(nom="Ahmed", prenom="Reda", email=email, role="etudiant", actif=True)
            utilisateur.set_password("password123")
            db.session.add(utilisateur)
            
        db.session.commit()
        print(f"Student {email} added.")
        
        for i in range(1, 5):
            envoyer_email_notification(
                destinataire=email,
                sujet=f"Test Email {i} - Hestim Schedule",
                corps=f"Bonjour Reda,\nCeci est l'email de test numéro {i} généré pour le rapport.\nCordialement."
            )
            print(f"Email {i} sent.")

if __name__ == '__main__':
    run_task()
