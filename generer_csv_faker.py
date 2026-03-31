import csv
import random
from datetime import date, timedelta, time as time_obj
from faker import Faker

fake = Faker('fr_FR')

def generate_csvs():
    print("Génération des fichiers CSV...")

    # Configuration des quantités
    nombre_etudiants = 150
    nombre_professeurs = 35
    nombre_salles = 20
    nombre_reservations = 2000

    # 1. etudiants.csv
    with open('etudiants.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nom', 'Prenom', 'Email', 'Niveau', 'Filiere'])
        filieres = ['Informatique', 'Mathématiques', 'Physique', 'Biologie']
        niveaux = ['L1', 'L2', 'L3', 'M1', 'M2']
        for _ in range(nombre_etudiants):
            prenom = fake.first_name()
            nom = fake.last_name()
            email = f"{prenom.lower()}.{nom.lower()}@etu.universite.fr"
            writer.writerow([nom, prenom, email, random.choice(niveaux), random.choice(filieres)])
    print(f" - etudiants.csv généré avec {nombre_etudiants} étudiants.")

    # 2. professeurs.csv
    profs_list = []
    with open('professeurs.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Nom', 'Prenom', 'Email', 'Specialite', 'Departement'])
        specialites = ['Algorithmique', 'Bases de données', 'IA', 'Réseaux', 'Algèbre', 'Mécanique quantique']
        departements = ['Département Info', 'Département Math', 'Département Phys']
        for _ in range(nombre_professeurs):
            prenom = fake.first_name()
            nom = fake.last_name()
            email = f"{prenom.lower()}.{nom.lower()}@universite.fr"
            specialite = random.choice(specialites)
            writer.writerow([nom, prenom, email, specialite, random.choice(departements)])
            profs_list.append(f"{nom} {prenom}")
    print(f" - professeurs.csv généré avec {nombre_professeurs} professeurs.")

    # 3. salles.csv
    salles_list = []
    with open('salles.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Numero_Salle', 'Batiment', 'Type_Salle', 'Capacite'])
        types_salle = ['amphi', 'classe', 'labo_informatique', 'labo_sciences', 'salle_reunion']
        batiments = ['Bâtiment A', 'Bâtiment B', 'Bâtiment C']
        for _ in range(nombre_salles):
            numero = f"{fake.bothify(text='?###', letters='ABCDE')}"
            writer.writerow([numero, random.choice(batiments), random.choice(types_salle), random.choice([20, 30, 40, 50, 100, 200])])
            salles_list.append(numero)
    print(f" - salles.csv généré avec {nombre_salles} salles.")

    # 4. reservations.csv
    with open('reservations.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID_Reservation', 'Professeur', 'Matiere', 'Salle', 'Date', 'Heure_Debut', 'Heure_Fin', 'Statut'])
        
        statuts = ['confirmee', 'en_attente', 'annulee']
        matieres = ['Maths', 'Physique', 'Info', 'Chimie', 'Histoire']
        
        for i in range(1, nombre_reservations + 1):
            prof = random.choice(profs_list)
            salle = random.choice(salles_list)
            matiere = random.choice(matieres)
            
            # Date aléatoire dans les 3 prochains mois
            jour = date.today() + timedelta(days=random.randint(1, 90))
            
            # Heure aléatoire
            hour = random.randint(8, 16)
            heure_debut = f"{hour:02d}:00"
            heure_fin = f"{hour + 1:02d}:30"
            
            statut = random.choices(statuts, weights=[80, 15, 5])[0] # 80% confirmées
            
            writer.writerow([i, prof, matiere, salle, jour.strftime("%Y-%m-%d"), heure_debut, heure_fin, statut])
            
    print(f" - reservations.csv généré avec {nombre_reservations} réservations.")

    print("\nTerminé ! Les 4 fichiers CSV ont été créés et mis à jour.")

if __name__ == "__main__":
    generate_csvs()
