from app import app, db
from models import Utilisateur, Professeur, Groupe, Salle, Cours, Creneau, Reservation
from datetime import datetime, date, timedelta, time as time_obj
import random

def simulate_group_schedule():
    with app.app_context():
        print("Demarrage de la simulation de l'emploi du temps...")

        # 1. Identifier ou créer le groupe "Cible" (Votre groupe)
        groupe_nom = "Groupe PACTE"
        groupe = Groupe.query.filter_by(nom_groupe=groupe_nom).first()
        if not groupe:
            groupe = Groupe(
                nom_groupe=groupe_nom, 
                niveau="4eme Année", 
                filiere="Génie Informatique", 
                annee_academique="2025-2026", 
                effectif=25
            )
            db.session.add(groupe)
            db.session.commit()
            print(f"Groupe '{groupe_nom}' cree.")
        else:
            print(f"Groupe '{groupe_nom}' trouve.")

        # 2. S'assurer d'avoir quelques professeurs et matières variées
        matieres_data = [
            ("Intelligence Artificielle", "IA401", "CM"),
            ("Machine Learning", "ML402", "TP"),
            ("Gestion de Projet", "MGT405", "TD"),
            ("Architecture Cloud", "CLD410", "CM"),
            ("Anglais Professionnel", "ENG404", "TD"),
            ("Développement Mobile", "MOB408", "TP")
        ]
        
        cours_crees = []
        
        # Récupérer quelques profs (ou en créer un par défaut)
        profs = Professeur.query.all()
        if not profs:
            prof = Professeur(nom="Martin", prenom="Jean", email="martin.jean@ecole.ma", specialite="Informatique")
            db.session.add(prof)
            db.session.commit()
            profs = [prof]

        for nom_cours, code, type_c in matieres_data:
            cours = Cours.query.filter_by(code_cours=code).first()
            if not cours:
                prof_aleatoire = random.choice(profs)
                cours = Cours(
                    nom_cours=nom_cours,
                    code_cours=code,
                    nombre_heures=30,
                    type_cours=type_c,
                    id_professeur=prof_aleatoire.id_professeur,
                    id_groupe=groupe.id_groupe,
                    semestre=2,
                    coefficient=2.0
                )
                db.session.add(cours)
                db.session.commit()
            cours_crees.append(cours)
        
        print(f"{len(cours_crees)} matieres pretes pour la simulation.")

        # 3. Générer le planning pour la semaine EN COURS (pour que ce soit visible demain)
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday()) # Lundi de cette semaine
        
        print(f"Generation du planning pour la semaine du {start_of_week.strftime('%d/%m/%Y')}...")

        salles = Salle.query.all()
        if not salles:
            print("Aucune salle trouvee ! Creez des salles d'abord.")
            return

        # Créneaux horaires standards
        slots_horaires = [
            (time_obj(8, 30), time_obj(10, 15), 'matin'),
            (time_obj(10, 30), time_obj(12, 15), 'matin'),
            (time_obj(13, 30), time_obj(15, 15), 'apres-midi'),
            (time_obj(15, 30), time_obj(17, 15), 'apres-midi')
        ]

        # Utilisateur admin pour "signer" la réservation (ou le premier user trouvé)
        admin = Utilisateur.query.filter_by(role='administrateur').first()
        if not admin:
            admin = Utilisateur.query.first() # Fallback

        compteur = 0
        for i in range(5): # Lundi à Vendredi
            current_day = start_of_week + timedelta(days=i)
            
            # On remplit ~3 créneaux par jour aléatoirement
            slots_du_jour = random.sample(slots_horaires, k=random.randint(2, 4))
            
            for debut, fin, periode in slots_du_jour:
                # 1. Créer/Récupérer le créneau
                creneau = Creneau.query.filter_by(jour=current_day, heure_debut=debut).first()
                if not creneau:
                    creneau = Creneau(jour=current_day, heure_debut=debut, heure_fin=fin, periode=periode)
                    db.session.add(creneau)
                    db.session.flush()

                # 2. Vérifier si le groupe est déjà occupé
                existe = Reservation.query.join(Cours).filter(
                    Cours.id_groupe == groupe.id_groupe,
                    Reservation.id_creneau == creneau.id_creneau,
                    Reservation.statut == 'confirmee'
                ).first()

                if not existe:
                    # Choisir un cours et une salle
                    cours_choisi = random.choice(cours_crees)
                    salle_choisie = random.choice(salles)

                    # Vérifier si la salle est libre
                    sala_occupied = Reservation.query.filter_by(
                        id_salle=salle_choisie.id_salle, 
                        id_creneau=creneau.id_creneau, 
                        statut='confirmee'
                    ).first()

                    if not sala_occupied:
                        res = Reservation(
                            id_cours=cours_choisi.id_cours,
                            id_salle=salle_choisie.id_salle,
                            id_creneau=creneau.id_creneau,
                            id_utilisateur=admin.id_utilisateur,
                            statut='confirmee',
                            commentaire="Simulation Soutenance"
                        )
                        db.session.add(res)
                        compteur += 1

        db.session.commit()
        print(f"Succes ! {compteur} cours ont ete ajoutes a l'emploi du temps de '{groupe_nom}'.")
        print("Connectez-vous en Admin, allez dans 'Emploi du temps' et filtrez sur ce groupe.")

if __name__ == '__main__':
    simulate_group_schedule()
