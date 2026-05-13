from app import app, db
from models import Utilisateur, Professeur, Cours, Groupe, Reservation, Creneau, Salle
from datetime import date, timedelta, time as time_obj
import random

def populate_prof_bousselham():
    with app.app_context():
        print("Remplissage du compte de M. Bousselham...")

        # 1. Récupérer le professeur
        email = 'prof@hestim.ma'
        prof = Professeur.query.filter_by(email=email).first()
        if not prof:
            print("Erreur: Professeur non trouve !")
            return

        print(f"Professeur trouve : {prof.prenom} {prof.nom}")

        # 2. Création de Cours Spécifiques (s'ils n'existent pas déjà liés à lui)
        # On va lui attribuer des cours variés pour la démo
        
        # Récupération de quelques groupes
        groupe_pacte = Groupe.query.filter_by(nom_groupe="Groupe PACTE").first()
        groupe_1a = Groupe.query.filter_by(nom_groupe="1A Tronc Commun").first()
        groupe_3a = Groupe.query.filter_by(nom_groupe="3A Génie Civil").first()
        
        courses_def = [
            {
                "nom": "Développement Web Fullstack",
                "code": "WEB-FULL-4",
                "type": "TP",
                "groupe": groupe_pacte,
                "heures": 40
            },
            {
                "nom": "Architecture Logicielle",
                "code": "ARCH-LOG-4",
                "type": "CM",
                "groupe": groupe_pacte,
                "heures": 30
            },
            {
                "nom": "Algorithmique Avancée",
                "code": "ALGO-102",
                "type": "TD",
                "groupe": groupe_1a,
                "heures": 20
            },
             {
                "nom": "Bases de Données Relationnelles",
                "code": "BDD-GC-3",
                "type": "CM",
                "groupe": groupe_3a,
                "heures": 25
            }
        ]

        my_courses = []
        for c in courses_def:
            if not c["groupe"]: continue
            
            cours = Cours.query.filter_by(code_cours=c["code"]).first()
            if not cours:
                cours = Cours(
                    nom_cours=c["nom"],
                    code_cours=c["code"],
                    nombre_heures=c["heures"],
                    type_cours=c["type"],
                    id_professeur=prof.id_professeur,
                    id_groupe=c["groupe"].id_groupe,
                    semestre=2,
                    coefficient=3.0
                )
                db.session.add(cours)
                db.session.commit()
                print(f"Cours cree : {c['nom']}")
            else:
                # S'assurer qu'il est bien assigné à ce prof pour la démo
                cours.id_professeur = prof.id_professeur
                db.session.commit()
                print(f"Cours reassigne : {c['nom']}")
            
            my_courses.append(cours)

        # 3. Génération de l'emploi du temps pour cette semaine
        print("\nGeneration des creneaux de la semaine...")
        
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        # Liste de créneaux fixes pour être sûr d'avoir un bel emploi du temps
        # Format: (Jour Index 0-4, Heure Debut, Heure Fin, Période)
        planning_target = [
            (0, time_obj(8, 30), time_obj(10, 15), 'matin'),      # Lundi matin
            (0, time_obj(13, 30), time_obj(15, 15), 'apres-midi'), # Lundi aprèm
            (1, time_obj(10, 30), time_obj(12, 15), 'matin'),      # Mardi fin matinée
            (2, time_obj(8, 30), time_obj(12, 15), 'matin'),       # Mercredi gros bloc (TP ?)
            (3, time_obj(15, 30), time_obj(17, 15), 'apres-midi'), # Jeudi fin d'aprèm
            (4, time_obj(10, 30), time_obj(12, 15), 'matin')       # Vendredi matin
        ]
        
        salles = Salle.query.all()
        admin_user = Utilisateur.query.filter_by(role='administrateur').first()
        
        for day_idx, start, end, periode in planning_target:
            current_day = start_of_week + timedelta(days=day_idx)
            
            # 1. Créer/Trouver le créneau
            creneau = Creneau.query.filter_by(jour=current_day, heure_debut=start).first()
            if not creneau:
                creneau = Creneau(jour=current_day, heure_debut=start, heure_fin=end, periode=periode)
                db.session.add(creneau)
                db.session.commit()
            
            # 2. Vérifier si le prof est déjà occupé (éviter doublons si on relance le script)
            occupied = Reservation.query.join(Cours).filter(
                Cours.id_professeur == prof.id_professeur,
                Reservation.id_creneau == creneau.id_creneau,
                Reservation.statut == 'confirmee'
            ).first()
            
            if not occupied:
                # Choisir un cours au hasard parmi ses cours
                cours_choisi = random.choice(my_courses)
                
                # Choisir une salle compatible et libre
                salle_choisie = None
                random.shuffle(salles)
                for s in salles:
                    # Vérif type salle vs type cours (sommaire)
                    if cours_choisi.type_cours == 'TP' and 'labo' not in s.type_salle: continue
                    
                    # Vérif disponibilité salle
                    salle_busy = Reservation.query.filter_by(
                        id_salle=s.id_salle, 
                        id_creneau=creneau.id_creneau,
                        statut='confirmee'
                    ).first()
                    
                    if not salle_busy:
                        salle_choisie = s
                        break
                
                if not salle_choisie:
                    # Fallback sur n'importe quelle salle libre
                    for s in salles:
                        salle_busy = Reservation.query.filter_by(id_salle=s.id_salle, id_creneau=creneau.id_creneau).first()
                        if not salle_busy:
                            salle_choisie = s
                            break
                            
                if salle_choisie:
                    # Créer la réservation
                    res = Reservation(
                        id_cours=cours_choisi.id_cours,
                        id_salle=salle_choisie.id_salle,
                        id_creneau=creneau.id_creneau,
                        id_utilisateur=admin_user.id_utilisateur if admin_user else 1,
                        statut='confirmee',
                        commentaire="Cours planifie pour demo"
                    )
                    db.session.add(res)
                    print(f"Ajout au planning : {current_day.strftime('%A')} {start.strftime('%H:%M')} - {cours_choisi.nom_cours}")
        
        db.session.commit()
        print("\nTermine ! M. Bousselham a un emploi du temps bien rempli.")

if __name__ == '__main__':
    populate_prof_bousselham()
