from app import app, db
from models import Utilisateur, Professeur, Etudiant, Groupe

def check_users():
    with app.app_context():
        print("Checking users...")
        
        # Check Teacher
        prof_email = "prof@hestim.ma"
        prof_user = Utilisateur.query.filter_by(email=prof_email).first()
        prof_obj = Professeur.query.filter_by(email=prof_email).first()
        print(f"Teacher User ({prof_email}): {'Found' if prof_user else 'Not Found'}")
        print(f"Teacher Profile ({prof_email}): {'Found' if prof_obj else 'Not Found'}")

        # Check Student
        student_email = "hajar.hamdouchi.1.1@hestim.ma"
        student_user = Utilisateur.query.filter_by(email=student_email).first()
        student_obj = Etudiant.query.filter_by(email=student_email).first()
        print(f"Student User ({student_email}): {'Found' if student_user else 'Not Found'}")
        
        groupe_nom = "Unknown"
        if student_obj:
            groupe = Groupe.query.get(student_obj.id_groupe) if student_obj.id_groupe else None
            groupe_nom = groupe.nom_groupe if groupe else "No Group"
            print(f"Student Profile: Found, Group: {groupe_nom}")
        else:
            print("Student Profile: Not Found (or Etudiant table check failed)")

if __name__ == "__main__":
    check_users()
