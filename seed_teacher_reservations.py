from app import app, db
from models import Utilisateur, Professeur, Etudiant, Groupe, Salle, Cours, Creneau, Reservation, Notification
from datetime import datetime, date, timedelta, time as time_obj
import random

def seed_teacher_data():
    with app.app_context():
        print("Creating/Checking Teacher User...")
        
        teacher_email = 'prof@hestim.ma'
        user = Utilisateur.query.filter_by(email=teacher_email).first()
        
        if not user:
            user = Utilisateur(
                nom='Bousselham',
                prenom='Mohammed',
                email=teacher_email,
                role='enseignant'
            )
            user.set_password('123456')
            db.session.add(user)
            db.session.commit()
            print(f"Created user: {user.email}")
        else:
            print(f"User exists: {user.email}")

        prof = Professeur.query.filter_by(email=teacher_email).first()
        if not prof:
            prof = Professeur(
                nom='Bousselham',
                prenom='Mohammed',
                email=teacher_email,
                specialite='Informatique',
                departement='Génie Informatique'
            )
            db.session.add(prof)
            db.session.commit()
            print("Created Professeur profile")
            
        # 3. Create reservations for the current week
        today = date.today()
        # Start from yesterday (Monday) or today if it's Monday
        start_of_week = today - timedelta(days=today.weekday())
        
        print(f"Seeding reservations for week of {start_of_week}...")
        
        # Get some resources
        salles = Salle.query.all()
        groupe = Groupe.query.first()
        if not groupe:
            print("No groups found! Creating one...")
            groupe = Groupe(nom_groupe="3A IIIA", niveau="3eme Annee", filiere="Genie Info", annee_scolaire="2025-2026", effectif=30)
            db.session.add(groupe)
            db.session.commit()

        # Create a course for this professor if none
        course = Cours.query.filter_by(code_cours="WEB301").first()
        if not course:
            course = Cours(
                nom_cours="Dev Web Fullstack",
                code_cours="WEB301",
                nombre_heures=40,
                type_cours="TP",
                id_professeur=prof.id_professeur,
                id_groupe=groupe.id_groupe,
                semestre=1,
                coefficient=3.0
            )
            db.session.add(course)
            db.session.commit()
            print("Created Course")
        else:
            print(f"Course exists: {course.nom_cours}")

        # Slots definition
        slots = [
            (time_obj(9, 0), time_obj(10, 45)),   # Matin 1
            (time_obj(11, 0), time_obj(12, 30)),  # Matin 2
            (time_obj(13, 30), time_obj(15, 15)), # PM 1
            (time_obj(15, 30), time_obj(17, 0))   # PM 2
        ]

        # Populate Monday to Friday
        for i in range(5): 
            current_day = start_of_week + timedelta(days=i)
            
            # Pick 2-3 random slots per day
            daily_slots = random.sample(slots, k=random.randint(2, 4))
            
            for start, end in daily_slots:
                # Check if slot exists or create it
                creneau = Creneau.query.filter_by(
                    jour=current_day,
                    heure_debut=start,
                    heure_fin=end
                ).first()
                
                if not creneau:
                    periode = 'matin' if start.hour < 12 else 'apres-midi'
                    creneau = Creneau(jour=current_day, heure_debut=start, heure_fin=end, periode=periode)
                    db.session.add(creneau)
                    db.session.flush()
                
                # Create reservation if not exists
                res = Reservation.query.filter_by(
                    id_creneau=creneau.id_creneau,
                    statut='confirmee'
                ).first()
                
                if not res:
                    salle = random.choice(salles)
                    reservation = Reservation(
                        id_cours=course.id_cours,
                        id_salle=salle.id_salle,
                        id_creneau=creneau.id_creneau,
                        id_utilisateur=user.id_utilisateur,
                        statut='confirmee',
                        commentaire='Test auto-generated'
                    )
                    db.session.add(reservation)
                    print(f"Added reservation: {current_day} {start.strftime('%H:%M')} - {course.nom_cours}")
        
        db.session.commit()
        print("Seeding complete!")

if __name__ == '__main__':
    seed_teacher_data()
