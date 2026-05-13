from app import app, db
from models import Utilisateur, Professeur, Groupe, Salle, Cours, Creneau, Reservation
from datetime import datetime, date, time as time_obj, timedelta
import random
from faker import Faker

fake = Faker('fr_FR')

def generate_fake_data(num_salles=5, num_groupes=3, num_profs=5, num_etudiants_per_groupe=15, num_cours=10, num_reservations_per_cours=2):
    with app.app_context():
        print("Début de la génération de données aléatoires...")

        # --- 1. Salles ---
        print("\nGénération des salles...")
        salles_creees = []
        types_salle = ['amphi', 'classe', 'labo_informatique', 'labo_sciences', 'salle_reunion']
        for _ in range(num_salles):
            salle = Salle(
                numero_salle=f"{fake.bothify(text='?###', letters='ABCDE')}",
                batiment=fake.random_element(elements=('Bâtiment A', 'Bâtiment B', 'Bâtiment C')),
                type_salle=random.choice(types_salle),
                capacite=random.choice([20, 30, 40, 50, 100, 200]),
                equipement_video=fake.boolean(chance_of_getting_true=50),
                equipement_informatique=fake.boolean(chance_of_getting_true=30),
                tableau_interactif=fake.boolean(chance_of_getting_true=20),
                climatisation=fake.boolean(chance_of_getting_true=60),
                statut='disponible'
            )
            # Check for unique room number
            while Salle.query.filter_by(numero_salle=salle.numero_salle).first():
                 salle.numero_salle = f"{fake.bothify(text='?###', letters='ABCDE')}"
            db.session.add(salle)
            salles_creees.append(salle)
        db.session.commit()
        print(f"{num_salles} salles créées.")

        # --- 2. Groupes ---
        print("\nGénération des groupes...")
        groupes_crees = []
        filieres = ['Informatique', 'Mathématiques', 'Physique', 'Biologie', 'Lettres']
        niveaux = ['L1', 'L2', 'L3', 'M1', 'M2']
        for _ in range(num_groupes):
            filiere = random.choice(filieres)
            niveau = random.choice(niveaux)
            groupe = Groupe(
                nom_groupe=f"Gr-{fake.bothify(text='??##')}-{filiere[:3]}",
                niveau=niveau,
                filiere=filiere,
                effectif=num_etudiants_per_groupe,
                annee_academique="2025-2026"
            )
             # Check for unique group name
            while Groupe.query.filter_by(nom_groupe=groupe.nom_groupe).first():
                groupe.nom_groupe = f"Gr-{fake.bothify(text='??##')}-{filiere[:3]}"
            db.session.add(groupe)
            groupes_crees.append(groupe)
        db.session.commit()
        print(f"{num_groupes} groupes créés.")

        # --- 3. Professeurs et Utilisateurs ---
        print("\nGénération des professeurs...")
        profs_crees = []
        specialites = ['Algorithmique', 'Bases de données', 'IA', 'Réseaux', 'Algèbre', 'Mécanique quantique']
        for _ in range(num_profs):
            prenom = fake.first_name()
            nom = fake.last_name()
            email = f"{prenom.lower()}.{nom.lower()}@universite.fr"
            
            # Check for unique email
            while Utilisateur.query.filter_by(email=email).first() or Professeur.query.filter_by(email=email).first():
                email = f"{prenom.lower()}.{nom.lower()}{fake.random_int(min=1, max=99)}@universite.fr"

            # Create User for professor
            user_prof = Utilisateur(
                nom=nom,
                prenom=prenom,
                email=email,
                role='enseignant'
            )
            user_prof.set_password('password123')
            db.session.add(user_prof)

            # Create Professor profile
            prof = Professeur(
                nom=nom,
                prenom=prenom,
                email=email,
                specialite=random.choice(specialites),
                telephone=fake.phone_number(),
                departement=random.choice(['Département Info', 'Département Math', 'Département Phys'])
            )
            db.session.add(prof)
            profs_crees.append(prof)
        db.session.commit()
        print(f"{num_profs} professeurs créés.")

        # --- 4. Étudiants et Utilisateurs ---
        print("\nGénération des étudiants...")
        for groupe in groupes_crees:
            for _ in range(num_etudiants_per_groupe):
                prenom = fake.first_name()
                nom = fake.last_name()
                email = f"{prenom.lower()}.{nom.lower()}@etu.universite.fr"
                
                # Check for unique email
                while Utilisateur.query.filter_by(email=email).first():
                     email = f"{prenom.lower()}.{nom.lower()}{fake.random_int(min=1, max=99)}@etu.universite.fr"

                # L'entité étudiant n'est pas complètement gérée dans votre DB (manque import ou table distincte Utilisateur_Etudiant selon le code, on crée l'Utilisateur)
                user_etu = Utilisateur(
                    nom=nom,
                    prenom=prenom,
                    email=email,
                    role='etudiant'
                )
                user_etu.set_password('password123')
                db.session.add(user_etu)
                
                # S'il y a un modèle Etudiant, vous pouvez l'ajouter ici
                # etu = Etudiant(nom=nom, prenom=prenom, email=email, id_groupe=groupe.id_groupe)
                # db.session.add(etu)
                
        db.session.commit()
        print(f"{num_groupes * num_etudiants_per_groupe} étudiants créés.")

        # --- 5. Cours ---
        print("\nGénération des cours...")
        cours_crees = []
        types_cours = ['CM', 'TD', 'TP']
        matieres = ['Maths', 'Physique', 'Info', 'Chimie', 'Histoire']
        for _ in range(num_cours):
             prof = random.choice(profs_crees)
             groupe = random.choice(groupes_crees)
             matiere = random.choice(matieres)
             nom_cours = f"{fake.catch_phrase()} ({matiere})"
             code_cours = f"{matiere[:3].upper()}{fake.unique.random_int(min=100, max=999)}"
             
             cours = Cours(
                 nom_cours=nom_cours,
                 code_cours=code_cours,
                 nombre_heures=random.choice([10, 20, 30]),
                 type_cours=random.choice(types_cours),
                 id_professeur=prof.id_professeur,
                 id_groupe=groupe.id_groupe,
                 semestre=random.choice([1, 2])
             )
             db.session.add(cours)
             cours_crees.append(cours)
        db.session.commit()
        print(f"{num_cours} cours créés.")

        # --- 6. Réservations ---
        print("\nGénération des réservations...")
        admin = Utilisateur.query.filter_by(role='administrateur').first()
        admin_id = admin.id_utilisateur if admin else 1

        reservations_ajoutees = 0
        for cours in cours_crees:
            for _ in range(num_reservations_per_cours):
                # Picks a random date within the next 30 days
                jour = date.today() + timedelta(days=random.randint(1, 30))
                
                # Picks a random start time (e.g., between 8 and 16)
                hour = random.randint(8, 16)
                start_time = time_obj(hour, 0)
                end_time = time_obj(hour + 1, 30) # 1.5 hour courses
                periode = 'matin' if hour < 13 else 'apres-midi'
                
                creneau = Creneau.query.filter_by(jour=jour, heure_debut=start_time, heure_fin=end_time).first()
                if not creneau:
                     creneau = Creneau(jour=jour, heure_debut=start_time, heure_fin=end_time, periode=periode)
                     db.session.add(creneau)
                     db.session.flush() # To get creneau ID
                
                salle = random.choice(salles_creees)
                
                # Simple conflict check
                conflit = Reservation.query.filter_by(id_creneau=creneau.id_creneau, id_salle=salle.id_salle).first()
                if not conflit:
                    reservation = Reservation(
                        id_cours=cours.id_cours,
                        id_salle=salle.id_salle,
                        id_creneau=creneau.id_creneau,
                        id_utilisateur=admin_id,
                        statut='confirmee',
                        commentaire="Réservation auto (Faker)"
                    )
                    db.session.add(reservation)
                    reservations_ajoutees += 1
        db.session.commit()
        print(f"{reservations_ajoutees} réservations ajoutées.")
        
        print("\n=== GÉNÉRATION TERMINÉE AVEC SUCCÈS ===")

if __name__ == "__main__":
    generate_fake_data()
