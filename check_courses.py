from app import app, db
from models import Groupe, Cours, Reservation, Creneau
from datetime import date

def list_group_courses():
    with app.app_context():
        # 1. Get Group ID
        groupe_nom = "1A-I"
        groupe = Groupe.query.filter_by(nom_groupe=groupe_nom).first()
        if not groupe:
            print(f"Group {groupe_nom} not found.")
            return

        print(f"Courses for Group {groupe_nom}:")
        courses = Cours.query.filter_by(id_groupe=groupe.id_groupe).all()
        for c in courses:
            print(f"- {c.nom_cours} ({c.code_cours})")

        # Check morning reservations
        today = date.today()
        print(f"\nReservations for today ({today}):")
        resas = Reservation.query.join(Creneau).filter(
            Creneau.jour == today,
            Reservation.statut == 'confirmee' # Assuming confirmed
        ).all()
        
        found = False
        for r in resas:
            c_obj = Cours.query.get(r.id_cours)
            if c_obj.id_groupe == groupe.id_groupe:
                print(f" - {r.creneau.heure_debut}: {c_obj.nom_cours}")
                found = True
        
        if not found:
            print("No other reservations found for this group today.")

if __name__ == "__main__":
    list_group_courses()
