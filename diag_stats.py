"""Script de diagnostic pour mes_statistiques"""
from flask import Flask
from database import db
from config import Config
from models import Professeur, Cours, Reservation, Creneau, Groupe, Salle
from datetime import datetime, date, timedelta
from sqlalchemy import func, distinct

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    profs_avec_reservations = db.session.query(Professeur).join(
        Cours, Cours.id_professeur == Professeur.id_professeur
    ).join(
        Reservation, Reservation.id_cours == Cours.id_cours
    ).filter(Reservation.statut == 'confirmee').distinct().limit(3).all()
    
    print(f"\n=== PROFESSEURS AVEC DES RÉSERVATIONS CONFIRMÉES ===")
    for prof in profs_avec_reservations:
        all_res = Reservation.query.join(Cours).filter(
            Cours.id_professeur == prof.id_professeur,
            Reservation.statut == 'confirmee'
        ).all()
        print(f"\nProf: {prof.prenom} {prof.nom} (email: {prof.email})")
        print(f"  Réservations confirmées: {len(all_res)}")
        
        if all_res:
            # Test taux_occupation_salle
            salles_utilisees = list(set(res.salle for res in all_res if res.salle))
            print(f"  Salles utilisées: {len(salles_utilisees)}")
            for s in salles_utilisees[:3]:
                print(f"    - {s.numero_salle}")
            
            # Test repartition_type_salle
            repartition = {}
            for res in all_res:
                t = res.salle.type_salle if res.salle else 'Inconnu'
                repartition[t] = repartition.get(t, 0) + 1
            print(f"  Types salles: {repartition}")
            
            # Test heatmap
            heatmap_jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
            heatmap_creneaux = ['08h', '09h', '10h', '11h', '12h', '13h', '14h', '15h', '16h', '17h']
            heatmap_grid = [[0] * len(heatmap_creneaux) for _ in range(len(heatmap_jours))]
            
            for res in all_res:
                if res.creneau:
                    jour_idx = res.creneau.jour.weekday()
                    if 0 <= jour_idx <= 5:
                        h_debut = res.creneau.heure_debut.hour
                        h_fin = res.creneau.heure_fin.hour
                        for h in range(h_debut, h_fin):
                            if 8 <= h <= 17:
                                heatmap_grid[jour_idx][h - 8] += 1
            
            total_heatmap = sum(sum(row) for row in heatmap_grid)
            print(f"  Total valeurs heatmap: {total_heatmap}")
            
            # Test semaine courante
            today = date.today()
            start_week = today - timedelta(days=today.weekday())
            end_week = start_week + timedelta(days=6)
            res_semaine = [r for r in all_res if start_week <= r.creneau.jour <= end_week]
            print(f"  Réservations cette semaine ({start_week} - {end_week}): {len(res_semaine)}")

    print("\n=== TEST TERMINÉ ===")
