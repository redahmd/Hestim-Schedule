from app import app, db
from models import Utilisateur, Professeur, Groupe, Salle, Cours, Creneau, Reservation
from datetime import datetime, date, time as time_obj

def add_specific_demo_reservation():
    with app.app_context():
        print("Ajout/Mise à jour du cours DÉMO pour les comptes spécifiés...")

        # 1. Configuration
        prof_email = "prof@hestim.ma"
        groupe_nom = "1A-I"
        salle_preferee = "A101" # Amphi A101
        
        today = date.today()
        start_time = time_obj(11, 00)
        end_time = time_obj(12, 30)

        print(f"Date: {today}, Heure: {start_time} - {end_time}")

        # 2. Récupérer les Acteurs
        # Professeur
        prof = Professeur.query.filter_by(email=prof_email).first()
        if not prof:
            print(f"ERREUR: Professeur {prof_email} introuvable dans la table Professeur.")
            return
        print(f"Professeur trouvé: {prof.nom} {prof.prenom}")

        # Groupe
        groupe = Groupe.query.filter_by(nom_groupe=groupe_nom).first()
        if not groupe:
            print(f"ERREUR: Groupe {groupe_nom} introuvable.")
            # Fallback if needed, but risky for the demo
            return
        print(f"Groupe trouvé: {groupe.nom_groupe}")

        # Salle
        salle = Salle.query.filter_by(numero_salle=salle_preferee).first()
        if not salle:
            salle = Salle.query.first()
        print(f"Salle utilisée: {salle.numero_salle}")

        # 3. Créneau
        creneau = Creneau.query.filter_by(jour=today, heure_debut=start_time).first()
        if not creneau:
            creneau = Creneau(jour=today, heure_debut=start_time, heure_fin=end_time, periode='matin')
            db.session.add(creneau)
            db.session.commit()

        # 4. Cours (Spécifique pour cette démo)
        cours_code = "DEMO_LIVE"
        cours = Cours.query.filter_by(code_cours=cours_code).first()
        
        # Si le cours existe déjà mais est assigné à quelqu'un d'autre ou un autre groupe, on le met à jour
        if cours:
            cours.id_professeur = prof.id_professeur
            cours.id_groupe = groupe.id_groupe
            cours.nom_cours = "DÉMO LIVE"
            db.session.commit()
            print("Cours 'DEMO_LIVE' mis à jour.")
        else:
            cours = Cours(
                nom_cours="DÉMO LIVE",
                code_cours=cours_code,
                nombre_heures=5,
                type_cours="CM",
                id_professeur=prof.id_professeur,
                id_groupe=groupe.id_groupe,
                semestre=1
            )
            db.session.add(cours)
            db.session.commit()
            print("Nouveau cours 'DEMO_LIVE' créé.")

        # 5. Nettoyage des conflits éventuels sur ce créneau
        # Supprimer toute réservation existante sur ce créneau pour ce prof OU cette salle
        conflits = Reservation.query.filter(
            Reservation.id_creneau == creneau.id_creneau,
            (Reservation.id_salle == salle.id_salle) | (Reservation.id_cours.in_(
                db.session.query(Cours.id_cours).filter_by(id_professeur=prof.id_professeur)
            ))
        ).all()
        
        for c in conflits:
            db.session.delete(c)
        if conflits:
            db.session.commit()
            print(f"{len(conflits)} conflit(s) supprimé(s).")

        # 6. Créer la Réservation
        admin = Utilisateur.query.filter_by(email="admin@hestim.ma").first()
        admin_id = admin.id_utilisateur if admin else 1

        reservation = Reservation(
            id_cours=cours.id_cours,
            id_salle=salle.id_salle,
            id_creneau=creneau.id_creneau,
            id_utilisateur=admin_id,
            statut='confirmee',
            commentaire="DÉMO LIVE PRÉSENTATION"
        )
        
        db.session.add(reservation)
        db.session.commit()

        print("\n=== SUCCÈS TOTAL ===")
        print(f"Le cours 'DÉMO LIVE' est planifié pour :")
        print(f" - Prof: {prof_email}")
        print(f" - Étudiant: hajar.hamdouchi.1.1@hestim.ma (Groupe {groupe.nom_groupe})")
        print(f" - Heure: 11h00 - 12h30")
        print(f" - Salle: {salle.numero_salle}")

if __name__ == "__main__":
    add_specific_demo_reservation()
