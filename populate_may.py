from app import app, db
from models import Utilisateur, Professeur, Groupe, Salle, Cours, Creneau, Reservation
from datetime import datetime, date, timedelta, time as time_obj
import random

def populate_may_2026():
    with app.app_context():
        print("Demarrage de la generation pour Mai 2026...")
        all_salles = Salle.query.all()
        all_profs = Professeur.query.all()
        
        # User Admin
        admin = Utilisateur.query.filter_by(role='administrateur').first()
        admin_id = admin.id_utilisateur if admin else 1

        slots_horaires = [
            (time_obj(8, 30), time_obj(10, 30), 'matin'),
            (time_obj(10, 30), time_obj(12, 30), 'matin'),
            (time_obj(13, 30), time_obj(15, 30), 'apres-midi'),
            (time_obj(15, 30), time_obj(17, 30), 'apres-midi')
        ]
        
        reservations_count = 0
        
        # May 2026 has 31 days. May 1st is Friday.
        start_date = date(2026, 5, 1)
        end_date = date(2026, 5, 31)
        
        current_day = start_date
        while current_day <= end_date:
            if current_day.weekday() < 5: # Lundi à Vendredi
                for debut, fin, periode in slots_horaires:
                    creneau = Creneau.query.filter_by(jour=current_day, heure_debut=debut).first()
                    if not creneau:
                        creneau = Creneau(jour=current_day, heure_debut=debut, heure_fin=fin, periode=periode)
                        db.session.add(creneau)
                        db.session.flush()
                    
                    groupes_all = Groupe.query.all()
                    for grp in groupes_all:
                        if random.random() > 0.3:
                            cours_du_groupe = Cours.query.filter_by(id_groupe=grp.id_groupe).all()
                            if not cours_du_groupe: continue
                            cours_choisi = random.choice(cours_du_groupe)
                            
                            prof_busy = Reservation.query.join(Cours).filter(
                                Cours.id_professeur == cours_choisi.id_professeur,
                                Reservation.id_creneau == creneau.id_creneau,
                                Reservation.statut == 'confirmee'
                            ).first()
                            
                            if prof_busy: continue
                            
                            groupe_busy = Reservation.query.join(Cours).filter(
                                Cours.id_groupe == grp.id_groupe,
                                Reservation.id_creneau == creneau.id_creneau,
                                Reservation.statut == 'confirmee'
                            ).first()
                            
                            if groupe_busy: continue
                            
                            candidate_salles = []
                            for s in all_salles:
                                if cours_choisi.type_cours == 'TP' and 'labo' not in s.type_salle: continue
                                if cours_choisi.type_cours == 'CM' and s.type_salle not in ['amphi', 'classe']: continue
                                
                                is_taken = Reservation.query.filter_by(
                                    id_salle=s.id_salle, 
                                    id_creneau=creneau.id_creneau, 
                                    statut='confirmee'
                                ).first()
                                
                                if not is_taken:
                                    candidate_salles.append(s)
                            
                            if candidate_salles:
                                salle_choisie = random.choice(candidate_salles)
                                res = Reservation(
                                    id_cours=cours_choisi.id_cours,
                                    id_salle=salle_choisie.id_salle,
                                    id_creneau=creneau.id_creneau,
                                    id_utilisateur=admin_id,
                                    statut='confirmee',
                                    commentaire="Simulation Mai 2026"
                                )
                                db.session.add(res)
                                reservations_count += 1
            current_day += timedelta(days=1)
        
        db.session.commit()
        print(f"Succes ! {reservations_count} reservations ajoutees pour le mois de Mai 2026.")

if __name__ == '__main__':
    populate_may_2026()
