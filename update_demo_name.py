from app import app, db
from models import Cours, Reservation, Creneau, Professeur, Groupe, Salle, Utilisateur
from datetime import date, time as time_obj

def update_demo_to_real():
    with app.app_context():
        print("Mise à jour du nom du cours de démo...")

        # 1. Retrouver le cours de démo
        code_demo = "DEMO_LIVE"
        cours = Cours.query.filter_by(code_cours=code_demo).first()

        if not cours:
            print("Cours DEMO_LIVE non trouvé. Création d'un nouveau cours 'Atelier Python'.")
            # Fallback logic if needed, but let's assume it exists from previous step
            # Create fresh if missing
            prof = Professeur.query.filter_by(email="prof@hestim.ma").first()
            groupe = Groupe.query.filter_by(nom_groupe="1A-I").first()
            cours = Cours(
                nom_cours="Atelier Python",
                code_cours="TP_PYT_ADV",
                nombre_heures=5,
                type_cours="TP",
                id_professeur=prof.id_professeur if prof else 1,
                id_groupe=groupe.id_groupe if groupe else 1,
                semestre=1
            )
            db.session.add(cours)
        else:
            # 2. Le renommer
            cours.nom_cours = "Atelier Python"
            cours.code_cours = "TP_PYT_ADV"
            cours.type_cours = "TP" # Plus logique pour un atelier
            print("Cours renommé en 'Atelier Python'.")

        db.session.commit()

        # 3. Vérifier la réservation
        today = date.today()
        start_time = time_obj(11, 00)
        
        # On cherche la résa liée à ce cours (maintenant TP_PYT_ADV)
        # Note: on a changé le code, mais l'ID reste le même, donc la résa pointe toujours dessus.
        # Mais au cas où on recrée :
        
        creneau = Creneau.query.filter_by(jour=today, heure_debut=start_time).first()
        if creneau:
            resa = Reservation.query.filter_by(id_creneau=creneau.id_creneau, id_cours=cours.id_cours).first()
            if resa:
                resa.commentaire = "Session Pratique"
                print("Réservation mise à jour.")
            else:
                 # Re-attach if lost (unlikely)
                 pass
        
        db.session.commit()
        print("\n=== MISE À JOUR TERMINÉE ===")
        print(f"Le cours de 11h00 s'appelle maintenant : {cours.nom_cours}")

if __name__ == "__main__":
    update_demo_to_real()
