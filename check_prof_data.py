from flask import Flask
from models import Reservation, Professeur, Cours
from database import db
from datetime import date
from config import Config
import os

def check_prof_data():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Get all professors
        profs = Professeur.query.all()
        print(f"Nombre de professeurs total: {len(profs)}")
        
        for prof in profs:
            # Check for confirmed reservations
            confirmed_res = Reservation.query.join(Cours).filter(
                Cours.id_professeur == prof.id_professeur,
                Reservation.statut == 'confirmee'
            ).count()
            
            if confirmed_res > 0:
                print(f"Prof: {prof.nom} {prof.prenom} (ID {prof.id_professeur}) a {confirmed_res} réservations confirmées.")
            else:
                # print(f"Prof: {prof.nom} {prof.prenom} a 0 réservations confirmées.")
                pass

if __name__ == "__main__":
    check_prof_data()
