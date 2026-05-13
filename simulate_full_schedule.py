from app import app, db
from models import Utilisateur, Professeur, Groupe, Salle, Cours, Creneau, Reservation
from datetime import datetime, date, timedelta, time as time_obj
import random

def simulate_full_school_schedule():
    with app.app_context():
        print("Demarrage de la simulation complete de l'ecole...")

        # --- 1. Salles & Equipements ---
        print("1. Generation des salles et equipements...")
        salles_data = [
            # Num, Bat, Type, Cap, Video, Info, Tab, Clim
            ("A101", "Batiment A", "amphi", 200, True, True, True, True),
            ("A102", "Batiment A", "amphi", 150, True, False, True, True),
            ("B201", "Batiment B", "classe", 40, False, False, True, False),
            ("B202", "Batiment B", "classe", 40, False, False, True, False),
            ("B203", "Batiment B", "classe", 30, True, False, False, False),
            ("L301", "Batiment C", "labo_informatique", 25, True, True, True, True),
            ("L302", "Batiment C", "labo_informatique", 25, True, True, False, True),
            ("S401", "Batiment D", "salle_reunion", 15, True, True, True, True), # Pour les etudiants (reunion projet)
            ("L402", "Batiment D", "labo_sciences", 20, False, False, True, True)
        ]

        all_salles = []
        for num, bat, typ, cap, vid, inf, tab, clim in salles_data:
            salle = Salle.query.filter_by(numero_salle=num).first()
            if not salle:
                salle = Salle(
                    numero_salle=num, batiment=bat, type_salle=typ, capacite=cap,
                    equipement_video=vid, equipement_informatique=inf, 
                    tableau_interactif=tab, climatisation=clim, statut='disponible'
                )
                db.session.add(salle)
            all_salles.append(salle)
        db.session.commit()
        all_salles = Salle.query.all() # Reload ids

        # --- 2. Professeurs ---
        print("2. Generation des professeurs...")
        profs_data = [
            ("Dr. Smith", "John", "Informatique"),
            ("Mme. Dubois", "Marie", "Mathematiques"),
            ("M. Martin", "Pierre", "Gestion"),
            ("Dr. Tanaka", "Ken", "Physique"),
            ("Mme. Johnson", "Sarah", "Anglais"),
            ("Filali", "Youssef", "Data Science"),
            ("M. Benali", "Ahmed", "Dev Web")
        ]
        
        all_profs = []
        for nom, prenom, spec in profs_data:
            email = f"{prenom.lower()}.{nom.lower().replace(' ', '').replace('.', '')}@hestim.ma"
            prof = Professeur.query.filter_by(email=email).first()
            if not prof:
                prof = Professeur(nom=nom, prenom=prenom, email=email, specialite=spec, departement="Sciences")
                db.session.add(prof)
            all_profs.append(prof)
        db.session.commit()
        all_profs = Professeur.query.all()

        # --- 3. Groupes & Cours ---
        print("3. Generation des groupes et des cours...")
        groupes_config = [
            {
                "nom": "1A Tronc Commun", 
                "niveau": "1ere Annee", 
                "matieres": [("Analyse I", "MATH101", "CM"), ("Algèbre", "MATH102", "TD"), ("Physique Méca", "PHY101", "CM"), ("Anglais", "ENG101", "TD")]
            },
            {
                "nom": "3A Génie Civil", 
                "niveau": "3eme Annee", 
                "matieres": [("RDM", "GC301", "CM"), ("Béton Armé", "GC302", "TP"), ("Hydraulique", "GC305", "TD"), ("Gestion Chantier", "GC310", "CM")]
            },
            {
                "nom": "Groupe PACTE", # Ton groupe
                "niveau": "4eme Annee", 
                "matieres": [("Intelligence Artificielle", "IA401", "CM"), ("Machine Learning", "ML402", "TP"), ("Gestion Projet", "MGT405", "TD"), ("Cloud Computing", "CLD410", "CM")]
            },
            {
                "nom": "5A Big Data", 
                "niveau": "5eme Annee", 
                "matieres": [("Deep Learning", "BD501", "TP"), ("Hadoop/Spark", "BD502", "TP"), ("Ethique IA", "ETH505", "CM"), ("Projet Fin Etude", "PFE599", "projet")]
            }
        ]

        # Creer les groupes et leurs cours
        cours_pool = [] # Liste de tuples (cours_obj, groupe_obj)
        
        for g_conf in groupes_config:
            groupe = Groupe.query.filter_by(nom_groupe=g_conf["nom"]).first()
            if not groupe:
                groupe = Groupe(nom_groupe=g_conf["nom"], niveau=g_conf["niveau"], filiere="Divers", effectif=30, annee_academique="2025-2026")
                db.session.add(groupe)
                db.session.commit() # Need ID immediately
            
            # Creer les cours pour ce groupe
            for nom_c, code_c, type_c in g_conf["matieres"]:
                cours = Cours.query.filter_by(code_cours=code_c).first()
                if not cours:
                    prof = random.choice(all_profs)
                    cours = Cours(
                        nom_cours=nom_c, code_cours=code_c, nombre_heures=30, type_cours=type_c,
                        id_professeur=prof.id_professeur, id_groupe=groupe.id_groupe, semestre=1 if "1" in code_c else 2
                    )
                    db.session.add(cours)
                    db.session.commit()
                cours_pool.append(cours)

        # --- 4. Generation du Planning ---
        print("4. Remplissage massif de l'emploi du temps...")
        
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday()) # Lundi
        
        slots_horaires = [
            (time_obj(8, 30), time_obj(10, 15), 'matin'),
            (time_obj(10, 30), time_obj(12, 15), 'matin'),
            (time_obj(13, 30), time_obj(15, 15), 'apres-midi'),
            (time_obj(15, 30), time_obj(17, 15), 'apres-midi')
        ]
        
        # User Admin pour signer
        admin = Utilisateur.query.filter_by(email='admin@hestim.ma').first() # Assuming standard admin
        if not admin:
            admin = Utilisateur.query.first()

        reservations_count = 0
        
        # Pour chaque jour de la semaine (Lundi-Vendredi)
        for i in range(5):
            current_day = start_of_week + timedelta(days=i)
            
            # Pour chaque créneau horaire
            for debut, fin, periode in slots_horaires:
                # Créer le créneau en base si inexistant
                creneau = Creneau.query.filter_by(jour=current_day, heure_debut=debut).first()
                if not creneau:
                    creneau = Creneau(jour=current_day, heure_debut=debut, heure_fin=fin, periode=periode)
                    db.session.add(creneau)
                    db.session.flush()
                
                # Pour chaque groupe, essayer de placer un cours
                groupes_all = Groupe.query.all()
                for grp in groupes_all:
                    # 70% de chance d'avoir cours ce créneau
                    if random.random() > 0.3:
                        # Trouver les cours de ce groupe
                        cours_du_groupe = Cours.query.filter_by(id_groupe=grp.id_groupe).all()
                        if not cours_du_groupe: continue
                        
                        cours_choisi = random.choice(cours_du_groupe)
                        
                        # Vérifier si le prof est libre
                        prof_busy = Reservation.query.join(Cours).filter(
                            Cours.id_professeur == cours_choisi.id_professeur,
                            Reservation.id_creneau == creneau.id_creneau,
                            Reservation.statut == 'confirmee'
                        ).first()
                        
                        if prof_busy: continue # Prof occupé, tant pis
                        
                        # Vérifier si le groupe est libre (déjà fait implicitement par la boucle, mais sécurité)
                        groupe_busy = Reservation.query.join(Cours).filter(
                            Cours.id_groupe == grp.id_groupe,
                            Reservation.id_creneau == creneau.id_creneau,
                            Reservation.statut == 'confirmee'
                        ).first()
                        
                        if groupe_busy: continue

                        # Trouver une salle libre adéquate
                        # Typiquement TP needs labo, CM needs Amphi or Classe
                        candidate_salles = []
                        for s in all_salles:
                             # Basic logic
                            if cours_choisi.type_cours == 'TP' and 'labo' not in s.type_salle: continue
                            if cours_choisi.type_cours == 'CM' and s.type_salle not in ['amphi', 'classe']: continue
                            
                            # Check availability
                            is_taken = Reservation.query.filter_by(
                                id_salle=s.id_salle, 
                                id_creneau=creneau.id_creneau, 
                                statut='confirmee'
                            ).first()
                            
                            if not is_taken:
                                candidate_salles.append(s)
                        
                        if candidate_salles:
                            salle_choisie = random.choice(candidate_salles)
                            
                            # Create Reservation
                            res = Reservation(
                                id_cours=cours_choisi.id_cours,
                                id_salle=salle_choisie.id_salle,
                                id_creneau=creneau.id_creneau,
                                id_utilisateur=admin.id_utilisateur if admin else 1,
                                statut='confirmee',
                                commentaire="Simulation"
                            )
                            db.session.add(res)
                            reservations_count += 1

        db.session.commit()
        print(f"Succes ! {reservations_count} reservations ajoutees pour la semaine.")
        print("L'admin devrait maintenant voir un planning bien rempli.")

if __name__ == '__main__':
    simulate_full_school_schedule()
