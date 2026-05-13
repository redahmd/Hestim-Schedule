from app import app, db
from models import Utilisateur, Professeur, Groupe, Salle, Cours, Creneau, Reservation
from datetime import datetime, date, time as time_obj

def add_demo_reservation():
    with app.app_context():
        print("Ajout d'un cours de démo pour AUJOURD'HUI à 11h00...")

        # 1. Date et Heure
        today = date.today() # 2026-02-06
        start_time = time_obj(11, 00)
        end_time = time_obj(12, 30)

        print(f"Date: {today}, Heure: {start_time} - {end_time}")

        # 2. Créer ou Récupérer le Créneau
        creneau = Creneau.query.filter_by(jour=today, heure_debut=start_time).first()
        if not creneau:
            creneau = Creneau(jour=today, heure_debut=start_time, heure_fin=end_time, periode='matin')
            db.session.add(creneau)
            db.session.commit()
            print(f"Créneau créé: ID {creneau.id_creneau}")
        else:
            print(f"Créneau existant trouvé: ID {creneau.id_creneau}")

        # 3. Sélectionner un Professeur (le premier trouvé ou un spécifique)
        # On essaie de prendre celui qui est probablement utilisé pour la démo
        # Ou on en prend un au hasard et on affiche son email pour le login
        prof = Professeur.query.first()
        if not prof:
            print("ERREUR: Aucun professeur trouvé !")
            return
        
        # Trouver l'utilisateur associé pour avoir ses credentials (email)
        user_prof = Utilisateur.query.filter_by(email=prof.email).first()
        print(f"Professeur sélectionné: {prof.nom} {prof.prenom} (Email: {prof.email})")

        # 4. Sélectionner un Groupe (pour l'étudiant)
        # On prend le 'Groupe PACTE' si possible, sinon le premier
        groupe = Groupe.query.filter_by(nom_groupe="Groupe PACTE").first()
        if not groupe:
            groupe = Groupe.query.first()
        
        if not groupe:
            print("ERREUR: Aucun groupe trouvé !")
            return
        
        print(f"Groupe sélectionné: {groupe.nom_groupe}")

        # 5. Créer ou Récupérer un Cours
        # Un cours qui lie ce prof et ce groupe
        nom_cours = "DÉMO PRÉSENTATION"
        code_cours = "DEMO101"
        
        cours = Cours.query.filter_by(code_cours=code_cours).first()
        if not cours:
            cours = Cours(
                nom_cours=nom_cours,
                code_cours=code_cours,
                nombre_heures=10,
                type_cours="CM",
                id_professeur=prof.id_professeur,
                id_groupe=groupe.id_groupe,
                semestre=1
            )
            db.session.add(cours)
            db.session.commit()
            print(f"Cours créé: {nom_cours}")
        else:
            # Update professor/group to match if needed, or just use it
            cours.id_professeur = prof.id_professeur
            cours.id_groupe = groupe.id_groupe
            db.session.commit()
            print(f"Cours existant utilisé: {nom_cours}")

        # 6. Sélectionner une Salle
        salle = Salle.query.filter_by(numero_salle="A101").first()
        if not salle:
            salle = Salle.query.first()
        print(f"Salle sélectionnée: {salle.numero_salle}")

        # 7. Créer la Réservation
        # D'abord, nettoyer s'il y a déjà une résa ce créneau pour cette salle/prof pour éviter les conflits
        existing_conflict = Reservation.query.filter_by(id_creneau=creneau.id_creneau, id_salle=salle.id_salle).first()
        if existing_conflict:
            db.session.delete(existing_conflict)
            db.session.commit()
            print("Conflit précédent supprimé.")

        # Admin user to be the 'creator'
        admin = Utilisateur.query.filter_by(role='administrateur').first()
        admin_id = admin.id_utilisateur if admin else 1

        reservation = Reservation(
            id_cours=cours.id_cours,
            id_salle=salle.id_salle,
            id_creneau=creneau.id_creneau,
            id_utilisateur=admin_id,
            statut='confirmee',
            commentaire="Créé pour la DÉMO LIVE"
        )
        
        db.session.add(reservation)
        db.session.commit()

        print("\n=== SUCCÈS ===")
        print(f"Réservation ajoutée pour AUJOURD'HUI ({today}) de 11h00 à 12h30.")
        print(f"Cours: {nom_cours}")
        print(f"Salle: {salle.numero_salle}")
        print(f"Prof: {prof.email} (Connectez-vous avec ce compte pour voir côté prof)")
        
        # Trouver un étudiant du groupe pour l'info
        # On cherche un utilisateur étudiant dont l'email pourrait correspondre à un étudiant (pas de lien direct easy en BD sauf si on a une table etudiant, mais ici on va juste dire 'Connectez vous en etudiant')
        print("Pour voir côté étudiant, connectez-vous avec un compte étudiant du groupe.")

if __name__ == "__main__":
    add_demo_reservation()
