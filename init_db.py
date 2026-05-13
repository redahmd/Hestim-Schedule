"""
Script d'initialisation de la base de données avec des données de test réalistes (Maroc)
"""
from flask import Flask
from config import Config
from database import db
from models import *
from werkzeug.security import generate_password_hash
from datetime import date, time, timedelta, datetime
import random

# Créer l'application Flask
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Données Marocaines
MOROCCAN_FIRST_NAMES_MALE = [
    "Mohamed", "Amine", "Yassine", "Omar", "Mehdi", "Youssef", "Hamza", "Bilal", 
    "Karim", "Anas", "Othmane", "Taha", "Zakaria", "Ismail", "Iliass", "Soufiane",
    "Ayoub", "Hassan", "Driss", "Rachid", "Khalid", "Samir", "Nabil", "Hicham"
]
MOROCCAN_FIRST_NAMES_FEMALE = [
    "Salma", "Sara", "Hiba", "Rim", "Ghita", "Zineb", "Noura", "Fatima", "Khadija",
    "Hajar", "Meryem", "Asmae", "Imane", "Houda", "Lamia", "Yasmine", "Chaimae",
    "Kaoutar", "Sanae", "Wiam", "Rania", "Aya", "Malak", "Nada"
]
MOROCCAN_LAST_NAMES = [
    "Alami", "Bennani", "Tazi", "Berrada", "El Idrissi", "Benjelloun", "Fassi", 
    "Chraibi", "Moussaoui", "Raji", "Kadiri", "Ouazzani", "Tahiri", "Hassani",
    "Jettou", "Sefrioui", "El Fassi", "Bouzoubaa", "Benkirane", "Filali", "Daoudi",
    "Amrani", "Naciri", "El Hajjaji", "Berraoui", "Zouiten", "Hamdouchi"
]

STREAMS = {
    "Informatique": ["Développement Web", "Bases de Données", "Algorithmique", "Réseaux", "Java", "Python"],
    "Management": ["Marketing", "Comptabilité", "Économie", "Gestion de Projet", "Droit des Affaires", "Res. Humaines"],
    "Génie Civil": ["RDM", "Béton Armé", "Hydraulique", "Topographie", "Matériaux", "Géotechnique"],
    "Génie Industriel": ["Logistique", "Recherche Opérationnelle", "Gestion de Production", "Qualité", "Maintenance", "Automatisme"]
}

def generate_moroccan_name():
    is_male = random.choice([True, False])
    first = random.choice(MOROCCAN_FIRST_NAMES_MALE if is_male else MOROCCAN_FIRST_NAMES_FEMALE)
    last = random.choice(MOROCCAN_LAST_NAMES)
    return first, last

def init_database():
    """Initialise la base de données avec des données de démonstration"""
    with app.app_context():
        print("Suppression des tables existantes...")
        db.drop_all()
        print("Création des tables...")
        db.create_all()

       
        print("Création de l'administrateur...")
        admin = Utilisateur(
            nom='Admin',
            prenom='Système',
            email='admin@hestim.ma',
            mot_de_passe=generate_password_hash('admin123'),
            role='administrateur'
        )
        db.session.add(admin)

       
        print("Création des groupes (classes)...")
        all_groups = []
        
      
        for filiere_name, subjects in STREAMS.items():
            for year in range(1, 6):
                
                suffix = "".join([word[0].upper() for word in filiere_name.split()])
                nom_groupe = f"{year}A-{suffix}"
                groupe = Groupe(
                    nom_groupe=nom_groupe,
                    niveau=f"{year}ère année",
                    filiere=filiere_name,
                    effectif=15, 
                    annee_academique='2025/2026'
                )
                db.session.add(groupe)
                all_groups.append(groupe)
        
        db.session.commit()

        # 3. Création des Étudiants (seed)
        print("Création des étudiants (15 par classe)...")
        etu_password = generate_password_hash('password123')
        
        all_students_users = []
        all_student_profiles = []
        
        for groupe in all_groups:
            for i in range(1, 16): # 15 students
                first, last = generate_moroccan_name()
                # Ensure unique email
                email = f"{first.lower()}.{last.lower()}.{groupe.id_groupe}.{i}@hestim.ma"
                
                # Create User Account
                u = Utilisateur(
                    nom=last,
                    prenom=first,
                    email=email,
                    mot_de_passe=etu_password,
                    role='etudiant'
                )
                all_students_users.append(u)
                
                # Create Student Profile
                s = Etudiant(
                    nom=last,
                    prenom=first,
                    email=email,
                    niveau=groupe.niveau,
                    id_groupe=groupe.id_groupe,
                    date_inscription=date(2023, 9, 1)
                )
                all_student_profiles.append(s)

        db.session.add_all(all_students_users)
        db.session.add_all(all_student_profiles)
        db.session.commit()

        # 4. Création des Professeurs
        print("Création des professeurs...")
        prof_password = generate_password_hash('password123')
        all_prof_users = []
        all_prof_profiles = []
        
        # Create about 30 professors to cover subjects
        prof_subjects = []
        for filiere, subjects in STREAMS.items():
            for subj in subjects:
                prof_subjects.append((subj, filiere))
        
        # Ensure we have enough profs, some can teach multiple
        unique_profs = []
        for i in range(30):
            first, last = generate_moroccan_name()
            email = f"{first.lower()}.{last.lower()}{i}@hestim.ma"
            
            u = Utilisateur(
                nom=last,
                prenom=first,
                email=email,
                mot_de_passe=prof_password,
                role='enseignant'
            )
            all_prof_users.append(u)
            
            # Assign a primarily Dept
            dept = random.choice(list(STREAMS.keys()))
            speciality = random.choice(STREAMS[dept])
            
            p = Professeur(
                nom=last,
                prenom=first,
                email=email,
                specialite=speciality,
                departement=dept,
                telephone=f"06{random.randint(10000000, 99999999)}"
            )
            all_prof_profiles.append(p)
            unique_profs.append(p)

        db.session.add_all(all_prof_users)
        db.session.add_all(all_prof_profiles)
        db.session.commit()

        # 5. Création des Salles
        print("Création des salles...")
        salles = []
        types = ['amphi', 'classe', 'labo_informatique', 'salle_reunion']
        for i in range(1, 21): # 20 Salles
            num = f"S{100+i}"
            s_type = random.choice(types)
            if i <= 5: s_type = 'classe' # Ensure enough classrooms
            
            s = Salle(
                numero_salle=num,
                batiment='Bâtiment Principal',
                type_salle=s_type,
                capacite=30,
                equipement_video=True,
                climatisation=True,
                statut='disponible'
            )
            salles.append(s)
        
        db.session.add_all(salles)
        db.session.commit()

        # 6. Création des Cours
        print("Création des cours...")
        courses = []
        for groupe in all_groups:
            # Assign 6 subjects per group
            filiere_subjects = STREAMS.get(groupe.filiere, STREAMS["Informatique"])
            
            for subject_name in filiere_subjects:
                # Find a prof who matches or random
                prof = next((p for p in unique_profs if p.specialite == subject_name), random.choice(unique_profs))
                
                c = Cours(
                    nom_cours=subject_name,
                    code_cours=f"{subject_name[:3].upper()}-{groupe.nom_groupe}",
                    nombre_heures=40,
                    type_cours='CM',
                    id_professeur=prof.id_professeur,
                    id_groupe=groupe.id_groupe,
                    semestre=1,
                    coefficient=random.choice([2.0, 3.0, 4.0])
                )
                courses.append(c)
        
        db.session.add_all(courses)
        db.session.commit()

        # 7. Algorithme de Génération d'Emploi du temps
        print("Lancement de l'algorithme de génération...")
        generation_emplois_du_temps(courses, salles, unique_profs)
        
        print("\n✅ Base de données initialisée avec succès!")
        print(f"   groupes: {len(all_groups)}")
        print(f"   étudiants: {len(all_student_profiles)}")
        print(f"   profs: {len(unique_profs)}")
        print(f"   cours: {len(courses)}")

def generation_emplois_du_temps(courses, salles, profs):
    """
    Algorithme simple de remplissage de créneaux.
    """
    
    # 1. Préparer les créneaux temporels (Lundi -> Vendredi, 4 créneaux par jour)
    # 08:30-10:30, 10:45-12:45, 14:00-16:00, 16:15-18:15
    today = date.today()
    monday = today - timedelta(days=today.weekday()) + timedelta(weeks=1) # Next Monday
    
    slots_defs = [
        (time(8, 30), time(10, 30), 'matin'),
        (time(10, 45), time(12, 45), 'matin'),
        (time(14, 00), time(16, 00), 'apres-midi'),
        (time(16, 15), time(18, 15), 'apres-midi')
    ]
    
    creneaux_objects = []
    # Create DB Creneaux for the week
    for day_offset in range(5): # Mon-Fri
        current_day = monday + timedelta(days=day_offset)
        for start, end, periode in slots_defs:
            c = Creneau(jour=current_day, heure_debut=start, heure_fin=end, periode=periode)
            db.session.add(c)
            creneaux_objects.append(c)
    db.session.commit()
    
    # Reload creneaux to get IDs
    creneaux_objects = Creneau.query.filter(Creneau.jour >= monday).all()
    
    # Dictionaries to track availability
    # Key: (id_creneau, entity_id) -> bool (True if busy)
    prof_busy = {}
    group_busy = {}
    room_busy = {} # Key: (id_creneau, room_id)
    
    reservations_to_add = []
    
    # Shuffle courses to distribute fairly
    random.shuffle(courses)
    
    for cours in courses:
        # Each course needs ~2 sessions this week
        sessions_needed = 2
        
        for _ in range(sessions_needed):
            assigned = False
            
            # Try to find a slot
            # Shuffle slots to avoid always picking Monday morning
            available_creneaux = creneaux_objects.copy()
            random.shuffle(available_creneaux)
            
            for creneau in available_creneaux:
                c_id = creneau.id_creneau
                
                # Check constraints
                if group_busy.get((c_id, cours.id_groupe)): continue
                if prof_busy.get((c_id, cours.id_professeur)): continue
                
                # Find a room
                found_room = None
                random.shuffle(salles)
                for salle in salles:
                    if not room_busy.get((c_id, salle.id_salle)):
                        found_room = salle
                        break
                
                if found_room:
                    # Create Reservation
                    # Note: We mark them as 'en_attente' for validation
                    res = Reservation(
                        id_cours=cours.id_cours,
                        id_salle=found_room.id_salle,
                        id_creneau=c_id,
                        id_utilisateur=1, # Admin
                        statut='en_attente', 
                        commentaire='Généré automatiquement'
                    )
                    reservations_to_add.append(res)
                    
                    # Mark busy
                    group_busy[(c_id, cours.id_groupe)] = True
                    prof_busy[(c_id, cours.id_professeur)] = True
                    room_busy[(c_id, found_room.id_salle)] = True
                    
                    assigned = True
                    break
            
            if not assigned:
                print(f"⚠️ Impossible de placer une séance pour {cours.nom_cours} (Groupe {cours.id_groupe})")

    db.session.add_all(reservations_to_add)
    db.session.commit()
    print(f"Génération terminée : {len(reservations_to_add)} réservations créées (en attente).")

if __name__ == '__main__':
    init_database()
