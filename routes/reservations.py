from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from database import db
from models import Reservation, Cours, Salle, Creneau, Notification
from datetime import datetime, date, time as time_obj, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import OperationalError, ProgrammingError

import csv
import io
from flask import Response

def envoyer_email_notification(destinataire, sujet, corps):
    """Fonction d'envoi d'email simulée pour la soutenance"""
    try:
        print(f"\n" + "="*50)
        print(f"📧 EMAIL SIMULÉ ENVOYÉ (via smtplib / Flask-Mail)")
        print(f"À      : {destinataire}")
        print(f"Sujet  : {sujet}")
        print(f"Message:\n{corps}")
        print("="*50 + "\n")
        return True
    except Exception as e:
        print(f"Erreur d'envoi d'email: {e}")
        return False

reservations_bp = Blueprint('reservations', __name__)

def _parse_iso_date(value, default_value):
    if not value:
        return default_value
    return datetime.strptime(value, '%Y-%m-%d').date()

def _daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

def _periode_from_heure_debut(heure_debut):
    if heure_debut < time_obj(12, 0):
        return 'matin'
    if heure_debut < time_obj(18, 0):
        return 'apres-midi'
    return 'soir'

def _jour_semaine_fr(jour_date):
    mapping = {
        0: 'lundi',
        1: 'mardi',
        2: 'mercredi',
        3: 'jeudi',
        4: 'vendredi',
        5: 'samedi',
        6: 'dimanche',
    }
    return mapping.get(jour_date.weekday())

def _build_disponibilites_cache(professeur_ids):
    try:
        from models import DisponibiliteProfesseur
        rows = (
            DisponibiliteProfesseur.query
            .filter(DisponibiliteProfesseur.id_professeur.in_(list(professeur_ids)))
            .all()
        )
        cache = {}
        for r in rows:
            cache.setdefault(r.id_professeur, []).append(r)
        return cache
    except (OperationalError, ProgrammingError):
        return None

def _professeur_est_disponible(id_professeur, jour_date, heure_debut, heure_fin, disponibilites_cache=None, forcer_disponibilites=False):
    try:
        if disponibilites_cache is None:
            from models import DisponibiliteProfesseur
            disponibilites = DisponibiliteProfesseur.query.filter_by(id_professeur=id_professeur).all()
        else:
            disponibilites = disponibilites_cache.get(id_professeur, [])

        if not disponibilites:
            return not forcer_disponibilites

        jour_semaine = _jour_semaine_fr(jour_date)
        if not jour_semaine:
            return False

        for d in disponibilites:
            if not d.disponible:
                continue
            if d.jour_semaine != jour_semaine:
                continue
            if d.date_debut and jour_date < d.date_debut:
                continue
            if d.date_fin and jour_date > d.date_fin:
                continue
            if d.heure_debut <= heure_debut and d.heure_fin >= heure_fin:
                return True
        return False
    except (OperationalError, ProgrammingError):
        return True

def _salle_rank_for_cours(salle, cours, effectif_groupe):
    score = 0

    if cours.type_cours == 'TP':
        if salle.type_salle in ('labo_informatique', 'labo_sciences'):
            score -= 20
    elif cours.type_cours in ('CM', 'examen'):
        if effectif_groupe >= 60 and salle.type_salle == 'amphi':
            score -= 20
        if effectif_groupe < 60 and salle.type_salle == 'classe':
            score -= 10
    else:
        if salle.type_salle == 'classe':
            score -= 5

    score += max(0, salle.capacite - effectif_groupe)
    return score

@reservations_bp.route('/')
@login_required
def liste():
    """Liste des r�servations"""
    from sqlalchemy.exc import OperationalError, ProgrammingError
    
    # Filtres
    statut = request.args.get('statut', '')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    salle_id = request.args.get('salle_id')
    type_cours = request.args.get('type_cours')
    professeur_id = request.args.get('professeur_id')
    groupe_id = request.args.get('groupe_id')

    # V�rifier si la table existe
    try:
        query = Reservation.query.options(
            joinedload(Reservation.creneau),
            joinedload(Reservation.cours).joinedload(Cours.professeur),
            joinedload(Reservation.cours).joinedload(Cours.groupe),
            joinedload(Reservation.salle)
        ).join(Creneau).join(Cours)

        # Filtrage selon le r�le
        if current_user.role == 'enseignant':
            from models import Professeur
            professeur = Professeur.query.filter_by(email=current_user.email).first()
            if professeur:
                query = query.filter(Cours.id_professeur == professeur.id_professeur)
        
        elif current_user.role == 'etudiant':
            from models import Etudiant
            etudiant = Etudiant.query.filter_by(email=current_user.email).first()
            if etudiant and etudiant.id_groupe:
                query = query.filter(Cours.id_groupe == etudiant.id_groupe)

        # Appliquer les filtres optionnels
        if statut:
            query = query.filter(Reservation.statut == statut)
        
        if date_debut:
            try:
                date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
                query = query.filter(Creneau.jour >= date_debut_obj)
            except (ValueError, TypeError):
                pass
        
        if date_fin:
            try:
                date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
                query = query.filter(Creneau.jour <= date_fin_obj)
            except (ValueError, TypeError):
                pass

        if salle_id:
            try:
                query = query.filter(Reservation.id_salle == int(salle_id))
            except (ValueError, TypeError):
                pass

        if type_cours:
            query = query.filter(Cours.type_cours == type_cours)

        if professeur_id:
            try:
                query = query.filter(Cours.id_professeur == int(professeur_id))
            except (ValueError, TypeError):
                pass

        if groupe_id:
            try:
                query = query.filter(Cours.id_groupe == int(groupe_id))
            except (ValueError, TypeError):
                pass
        
        reservations = query.order_by(Creneau.jour.desc(), Creneau.heure_debut).all()

    except (OperationalError, ProgrammingError):
        # Table n'existe pas encore
        reservations = []

    # Donn�es pour les filtres avanc�s (admin seulement)
    salles = []
    professeurs = []
    groupes = []
    
    if current_user.role == 'administrateur':
        try:
            from models import Salle as SalleModel, Professeur, Groupe
            salles = SalleModel.query.order_by(SalleModel.numero_salle).all()
            professeurs = Professeur.query.order_by(Professeur.prenom, Professeur.nom).all()
            groupes = Groupe.query.order_by(Groupe.nom_groupe).all()
        except (OperationalError, ProgrammingError):
            pass

    return render_template(
        'reservations/liste.html',
        reservations=reservations,
        statut=statut,
        date_debut=date_debut,
        date_fin=date_fin,
        salle_id=salle_id,
        type_cours=type_cours,
        professeur_id=professeur_id,
        groupe_id=groupe_id,
        salles=salles,
        professeurs=professeurs,
        groupes=groupes,
    )


@reservations_bp.route('/export')
@login_required
def export():
    """Export CSV simple des r�servations selon les filtres actuels."""
    import csv
    from io import StringIO

    statut = request.args.get('statut', 'confirmee')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')

    try:
        query = Reservation.query.join(Creneau).join(Cours)

        if statut:
            query = query.filter(Reservation.statut == statut)

        if date_debut:
            query = query.filter(Creneau.jour >= datetime.strptime(date_debut, '%Y-%m-%d').date())

        if date_fin:
            query = query.filter(Creneau.jour <= datetime.strptime(date_fin, '%Y-%m-%d').date())

        # Filtrage selon le r�le (m�mes r�gles que la liste)
        if current_user.role == 'enseignant':
            from models import Professeur
            professeur = Professeur.query.filter_by(email=current_user.email).first()
            if professeur:
                query = query.filter(Cours.id_professeur == professeur.id_professeur)
        elif current_user.role == 'etudiant':
            from models import Etudiant
            etudiant = Etudiant.query.filter_by(email=current_user.email).first()
            if etudiant and etudiant.id_groupe:
                query = query.filter(Cours.id_groupe == etudiant.id_groupe)

        reservations = query.order_by(Creneau.jour, Creneau.heure_debut).all()

        si = StringIO()
        writer = csv.writer(si, delimiter=';')
        writer.writerow(['Date', 'Heure d�but', 'Heure fin', 'Cours', 'Salle', 'Professeur', 'Groupe', 'Statut'])

        for r in reservations:
            writer.writerow([
                r.creneau.jour.strftime('%Y-%m-%d'),
                r.creneau.heure_debut.strftime('%H:%M'),
                r.creneau.heure_fin.strftime('%H:%M'),
                f'{r.cours.code_cours} - {r.cours.nom_cours}',
                r.salle.numero_salle,
                f'{r.cours.professeur.prenom} {r.cours.professeur.nom}',
                r.cours.groupe.nom_groupe,
                r.statut,
            ])

        from flask import Response
        output = si.getvalue()
        return Response(
            output,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=reservations.csv'}
        )
    except (OperationalError, ProgrammingError):
        from flask import Response
        return Response('', mimetype='text/csv')


@reservations_bp.route('/planning')
@login_required
def planning():
    """Vue planning grille d�taill�e style Excel."""
    semaine_str = request.args.get('semaine')
    if semaine_str:
        try:
            start_date = datetime.strptime(semaine_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = date.today() - timedelta(days=date.today().weekday())
    else:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
        semaine_str = start_date.strftime('%Y-%m-%d')

    end_date = start_date + timedelta(days=6)

    try:
        query = Reservation.query.options(
            joinedload(Reservation.creneau),
            joinedload(Reservation.cours).joinedload(Cours.professeur),
            joinedload(Reservation.cours).joinedload(Cours.groupe),
            joinedload(Reservation.salle)
        ).join(Creneau).join(Cours).join(Salle)
        
        query = query.filter(
            Creneau.jour >= start_date,
            Creneau.jour <= end_date,
            Reservation.statut == 'confirmee'
        )

        # Filtres
        if current_user.role == 'enseignant':
            from models import Professeur
            professeur = Professeur.query.filter_by(email=current_user.email).first()
            if professeur:
                query = query.filter(Cours.id_professeur == professeur.id_professeur)
        elif current_user.role == 'etudiant':
            from models import Etudiant
            etudiant = Etudiant.query.filter_by(email=current_user.email).first()
            if etudiant and etudiant.id_groupe:
                query = query.filter(Cours.id_groupe == etudiant.id_groupe)

        reservations = query.order_by(Creneau.jour, Creneau.heure_debut).all()

        # Structure de donn�es pour la grille
        # On veut une liste de jours avec 4 cr�neaux fixes
        planning_grid = []
        current = start_date
        jours_fr = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
        mois_fr = {1:'janvier', 2:'f�vrier', 3:'mars', 4:'avril', 5:'mai', 6:'juin', 7:'juillet', 8:'ao�t', 9:'septembre', 10:'octobre', 11:'novembre', 12:'d�cembre'}

        while current <= end_date:
            day_data = {
                'date_obj': current,
                'date_str': f"{jours_fr[current.weekday()]} {current.day} {mois_fr[current.month]} {current.year}",
                'slots': {
                    'matin1': None, # 09h00-10h45
                    'matin2': None, # 11h00-12h30
                    'pm1': None,    # 13h30-15h15
                    'pm2': None     # 15h30-17h00
                }
            }
            
            # Remplir les slots avec les r�servations
            day_res = [r for r in reservations if r.creneau.jour == current]
            for r in day_res:
                t = r.creneau.heure_debut
                # Logique de mapping approximative des cr�neaux
                slot_key = None
                if t < time_obj(11, 0):
                    slot_key = 'matin1'
                elif t < time_obj(13, 30):
                    slot_key = 'matin2'
                elif t < time_obj(15, 30):
                    slot_key = 'pm1'
                else:
                    slot_key = 'pm2'
                
                if slot_key and not day_data['slots'][slot_key]:
                     # Pr�parer les donn�es d'affichage
                    prof_nom = f"{r.cours.professeur.nom.upper()} {r.cours.professeur.prenom}" if r.cours.professeur else "N/A"
                    day_data['slots'][slot_key] = {
                        'matiere': r.cours.nom_cours,
                        'enseignant': prof_nom,
                        'salle': r.salle.numero_salle,
                        'batiment': r.salle.batiment,
                        'groupe': r.cours.groupe.nom_groupe if r.cours.groupe else "",
                        'type': r.cours.type_cours,
                        'heure': f"{r.creneau.heure_debut.strftime('%Hh%M')}-{r.creneau.heure_fin.strftime('%Hh%M')}",
                        'iso_date': r.creneau.jour.isoformat(),
                        'iso_start': r.creneau.heure_debut.strftime('%H:%M:%S'),
                        'iso_end': r.creneau.heure_fin.strftime('%H:%M:%S')
                    }
            
            planning_grid.append(day_data)
            current += timedelta(days=1)

    except (OperationalError, ProgrammingError):
        planning_grid = []

    return render_template(
        'reservations/planning.html',
        planning_grid=planning_grid,
        semaine_str=semaine_str,
    )

@reservations_bp.route('/planning/export')
@login_required
def export_planning():
    """Exporter le planning hebdomadaire en CSV"""
    if current_user.role != 'administrateur':
        flash('Acc�s refus�.', 'error')
        return redirect(url_for('reservations.planning'))

    semaine_str = request.args.get('semaine')
    
    if not semaine_str:
        today = date.today()
        start_date = today - timedelta(days=today.weekday())
    else:
        try:
            start_date = datetime.strptime(semaine_str, '%Y-%m-%d').date()
        except ValueError:
            today = date.today()
            start_date = today - timedelta(days=today.weekday())
            
    end_date = start_date + timedelta(days=6)
    
    # R�cup�rer les r�servations (m�me requ�te que planning)
    reservations = Reservation.query.join(Creneau).options(
        joinedload(Reservation.cours).joinedload(Cours.professeur),
        joinedload(Reservation.cours).joinedload(Cours.groupe),
        joinedload(Reservation.salle),
        joinedload(Reservation.creneau)
    ).filter(
        Reservation.statut == 'confirmee',
        Creneau.jour >= start_date,
        Creneau.jour <= end_date
    ).order_by(Creneau.jour, Creneau.heure_debut).all()
    
    # Cr�ation du CSV
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # En-t�tes
    writer.writerow(['Date', 'Heure D�but', 'Heure Fin', 'Code Cours', 'Mati�re', 'Semestre', 'Salle', 'B�timent', 'Groupe', 'Professeur', 'Type'])
    
    jours_fr = {0: 'Lundi', 1: 'Mardi', 2: 'Mercredi', 3: 'Jeudi', 4: 'Vendredi', 5: 'Samedi', 6: 'Dimanche'}
    
    for res in reservations:
        jour_nom = jours_fr.get(res.creneau.jour.weekday(), '')
        date_fmt = f"{jour_nom} {res.creneau.jour.strftime('%d/%m/%Y')}"
        
        prof_nom = 'N/A'
        if res.cours.professeur:
            prof_nom = f"{res.cours.professeur.prenom} {res.cours.professeur.nom}"
            
        groupe_nom = res.cours.groupe.nom_groupe if res.cours.groupe else 'N/A'
        
        writer.writerow([
            date_fmt,
            res.creneau.heure_debut.strftime('%H:%M'),
            res.creneau.heure_fin.strftime('%H:%M'),
            res.cours.code_cours,
            res.cours.nom_cours,
            res.cours.semestre or '',
            res.salle.numero_salle,
            res.salle.batiment or '',
            groupe_nom,
            prof_nom,
            res.cours.type_cours
        ])
    
    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=planning_hestim_{start_date.strftime('%Y_%m_%d')}.csv"}
    )

@reservations_bp.route('/export_ics')
@login_required
def export_ics():
    """Export des r�servations au format iCalendar (.ics)"""
    
    try:
        # Par d�faut: Export de TOUT ce qui est � venir + 1 mois pass�
        start_date = date.today() - timedelta(days=30)
        
        query = Reservation.query.options(
            joinedload(Reservation.creneau),
            joinedload(Reservation.cours).joinedload(Cours.professeur),
            joinedload(Reservation.cours).joinedload(Cours.groupe),
            joinedload(Reservation.salle)
        ).join(Creneau).join(Cours).join(Salle)
        
        query = query.filter(
            Creneau.jour >= start_date,
            Reservation.statut == 'confirmee'
        )

        # Filtres User
        if current_user.role == 'enseignant':
            from models import Professeur
            professeur = Professeur.query.filter_by(email=current_user.email).first()
            if professeur:
                query = query.filter(Cours.id_professeur == professeur.id_professeur)
        elif current_user.role == 'etudiant':
            from models import Etudiant
            etudiant = Etudiant.query.filter_by(email=current_user.email).first()
            if etudiant and etudiant.id_groupe:
                query = query.filter(Cours.id_groupe == etudiant.id_groupe)

        reservations = query.order_by(Creneau.jour, Creneau.heure_debut).all()

        # 2. G�n�rer le contenu ICS
        ics_content = []
        ics_content.append("BEGIN:VCALENDAR")
        ics_content.append("VERSION:2.0")
        ics_content.append("PRODID:-//Hestim Schedule//FR")
        ics_content.append("CALSCALE:GREGORIAN")
        ics_content.append("METHOD:PUBLISH")
        
        now_str = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

        for r in reservations:
            # Dates
            dt_start = datetime.combine(r.creneau.jour, r.creneau.heure_debut)
            dt_end = datetime.combine(r.creneau.jour, r.creneau.heure_fin)
            
            # Format: YYYYMMDDTHHMMSS
            dt_start_str = dt_start.strftime('%Y%m%dT%H%M%S')
            dt_end_str = dt_end.strftime('%Y%m%dT%H%M%S')
            
            # Infos
            summary = f"{r.cours.nom_cours} ({r.cours.type_cours})"
            location = f"Salle {r.salle.numero_salle} - {r.salle.batiment or ''}"
            
            prof_nom = "N/A"
            if r.cours.professeur:
                prof_nom = f"{r.cours.professeur.prenom} {r.cours.professeur.nom}"
                
            groupe_nom = r.cours.groupe.nom_groupe if r.cours.groupe else "N/A"
            
            description = f"Prof: {prof_nom}\\nGroupe: {groupe_nom}\\nType: {r.cours.type_cours}"
            
            # Unique ID
            uid = f"res-{r.id_reservation}@hestim-schedule.local"

            ics_content.append("BEGIN:VEVENT")
            ics_content.append(f"UID:{uid}")
            ics_content.append(f"DTSTAMP:{now_str}")
            ics_content.append(f"DTSTART:{dt_start_str}")
            ics_content.append(f"DTEND:{dt_end_str}")
            ics_content.append(f"SUMMARY:{summary}")
            ics_content.append(f"LOCATION:{location}")
            ics_content.append(f"DESCRIPTION:{description}")
            ics_content.append("END:VEVENT")

        ics_content.append("END:VCALENDAR")
        
        output = "\\r\\n".join(ics_content)
        
        return Response(
            output,
            mimetype="text/calendar",
            headers={"Content-Disposition": f"attachment;filename=planning_hestim.ics"}
        )

    except Exception as e:
        return Response(f"Erreur lors de la g�n�ration du calendrier: {str(e)}", status=500)

@reservations_bp.route('/creer', methods=['GET', 'POST'])
@login_required
def creer():
    """Cr�er une nouvelle r�servation"""
    from models import Cours, Salle, Creneau
    from sqlalchemy.exc import OperationalError, ProgrammingError
    
    if request.method == 'POST':
        try:
            id_cours = request.form.get('id_cours')
            id_salle = request.form.get('id_salle')
            jour = request.form.get('jour')
            heure_debut = request.form.get('heure_debut')
            heure_fin = request.form.get('heure_fin')
            commentaire = request.form.get('commentaire', '').strip()
            
            # Validation des champs obligatoires
            if not all([id_cours, id_salle, jour, heure_debut, heure_fin]):
                flash('Veuillez remplir tous les champs obligatoires', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # V�rifier que le cours existe
            cours = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).get(id_cours)
            if not cours:
                flash('Cours introuvable', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # V�rifier la capacit� de la salle
            salle = Salle.query.get(id_salle)
            if not salle:
                flash('Salle introuvable', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            if salle.capacite < cours.groupe.effectif:
                flash(f'La capacit� de la salle ({salle.capacite}) est insuffisante pour le groupe ({cours.groupe.effectif} �tudiants)', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # Validation des dates et heures
            try:
                jour_date = datetime.strptime(jour, '%Y-%m-%d').date()
                heure_debut_time = datetime.strptime(heure_debut, '%H:%M').time()
                heure_fin_time = datetime.strptime(heure_fin, '%H:%M').time()
            except ValueError:
                flash('Format de date ou d\'heure invalide', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # V�rifier que l'heure de fin est apr�s l'heure de d�but
            if heure_fin_time <= heure_debut_time:
                flash('L\'heure de fin doit �tre apr�s l\'heure de d�but', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # V�rifier que la date n'est pas dans le pass�
            if jour_date < date.today():
                flash('Vous ne pouvez pas r�server une date dans le pass�', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # D�terminer la p�riode
            if heure_debut_time < time_obj(12, 0):
                periode = 'matin'
            elif heure_debut_time < time_obj(18, 0):
                periode = 'apres-midi'
            else:
                periode = 'soir'
            
            # Cr�er ou trouver le cr�neau
            creneau = Creneau.query.filter_by(
                jour=jour_date,
                heure_debut=heure_debut_time,
                heure_fin=heure_fin_time
            ).first()
            
            if not creneau:
                creneau = Creneau(
                    jour=jour_date,
                    heure_debut=heure_debut_time,
                    heure_fin=heure_fin_time,
                    periode=periode
                )
                db.session.add(creneau)
                db.session.flush()
            
            # V�rifier les conflits
            conflit_salle = Reservation.query.filter_by(
                id_salle=id_salle,
                id_creneau=creneau.id_creneau,
                statut='confirmee'
            ).first()
            
            if conflit_salle:
                flash('Cette salle est d�j� r�serv�e pour ce cr�neau', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # V�rifier conflit professeur
            conflit_prof = Reservation.query.join(Cours).filter(
                Cours.id_professeur == cours.id_professeur,
                Reservation.id_creneau == creneau.id_creneau,
                Reservation.statut == 'confirmee'
            ).first()
            
            if conflit_prof:
                flash('Le professeur a d�j� un cours � ce cr�neau', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # V�rifier conflit groupe
            conflit_groupe = Reservation.query.join(Cours).filter(
                Cours.id_groupe == cours.id_groupe,
                Reservation.id_creneau == creneau.id_creneau,
                Reservation.statut == 'confirmee'
            ).first()
            
            if conflit_groupe:
                flash('Le groupe a d�j� un cours � ce cr�neau', 'error')
                cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
            
            # Cr�er la r�servation
            reservation = Reservation(
                id_cours=id_cours,
                id_salle=id_salle,
                id_creneau=creneau.id_creneau,
                id_utilisateur=current_user.id_utilisateur,
                statut='confirmee',
                commentaire=commentaire
            )
            
            db.session.add(reservation)
            db.session.flush()
            
            # Cr�er une notification
            try:
                notification = Notification(
                    id_utilisateur=current_user.id_utilisateur,
                    type_notification='reservation',
                    message=f'R�servation confirm�e pour {cours.nom_cours} le {jour_date.strftime("%d/%m/%Y")}',
                    id_reservation=reservation.id_reservation
                )
                db.session.add(notification)
            except (OperationalError, ProgrammingError):
                # Table notification n'existe pas encore, on continue sans notification
                pass
            
            db.session.commit()
            
            flash('R�servation cr��e avec succ�s ! ??', 'success')
            return redirect(url_for('reservations.detail', id=reservation.id_reservation))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la cr�ation de la r�servation: {str(e)}', 'error')
            cours_list = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur)).all()
            salles_list = Salle.query.filter_by(statut='disponible').all()
            return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)
    
    # GET: Afficher le formulaire
    try:
        query = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur))
        
        # Pour les enseignants, ne montrer que leurs cours
        if current_user.role == 'enseignant':
            from models import Professeur
            professeur = Professeur.query.filter_by(email=current_user.email).first()
            if professeur:
                query = query.filter(Cours.id_professeur == professeur.id_professeur)
        
        cours_list = query.order_by(Cours.code_cours).all()
        salles_list = Salle.query.filter_by(statut='disponible').order_by(Salle.numero_salle).all()
    except (OperationalError, ProgrammingError):
        cours_list = []
        salles_list = []
    
    return render_template('reservations/creer.html', cours_list=cours_list, salles_list=salles_list)

@reservations_bp.route('/verifier-disponibilite', methods=['POST'])
@login_required
def verifier_disponibilite():
    """API pour v�rifier la disponibilit� d'une salle pour un cr�neau"""
    from models import Salle, Creneau
    from sqlalchemy.exc import OperationalError, ProgrammingError
    
    try:
        data = request.get_json()
        jour = data.get('jour')
        heure_debut = data.get('heure_debut')
        heure_fin = data.get('heure_fin')
        salle_id = data.get('salle_id')
        cours_id = data.get('cours_id')
        
        if not all([jour, heure_debut, heure_fin]):
            return jsonify({'disponible': False, 'message': 'Param�tres manquants'}), 400
        
        # Parser les dates
        jour_date = datetime.strptime(jour, '%Y-%m-%d').date()
        heure_debut_time = datetime.strptime(heure_debut, '%H:%M').time()
        heure_fin_time = datetime.strptime(heure_fin, '%H:%M').time()
        
        # V�rifier si le cr�neau existe
        creneau = Creneau.query.filter_by(
            jour=jour_date,
            heure_debut=heure_debut_time,
            heure_fin=heure_fin_time
        ).first()
        
        if not creneau:
            # Cr�neau n'existe pas encore, donc disponible
            return jsonify({'disponible': True, 'message': 'Cr�neau disponible'})
        
        # V�rifier les conflits
        conflits = []
        
        if salle_id:
            conflit_salle = Reservation.query.filter_by(
                id_salle=salle_id,
                id_creneau=creneau.id_creneau,
                statut='confirmee'
            ).first()
            if conflit_salle:
                conflits.append('Cette salle est d�j� r�serv�e pour ce cr�neau')
        
        if cours_id:
            cours = Cours.query.get(cours_id)
            if cours:
                # V�rifier conflit professeur
                conflit_prof = Reservation.query.join(Cours).filter(
                    Cours.id_professeur == cours.id_professeur,
                    Reservation.id_creneau == creneau.id_creneau,
                    Reservation.statut == 'confirmee'
                ).first()
                if conflit_prof:
                    conflits.append('Le professeur a d�j� un cours � ce cr�neau')
                
                # V�rifier conflit groupe
                conflit_groupe = Reservation.query.join(Cours).filter(
                    Cours.id_groupe == cours.id_groupe,
                    Reservation.id_creneau == creneau.id_creneau,
                    Reservation.statut == 'confirmee'
                ).first()
                if conflit_groupe:
                    conflits.append('Le groupe a d�j� un cours � ce cr�neau')
        
        if conflits:
            return jsonify({
                'disponible': False,
                'message': '; '.join(conflits),
                'conflits': conflits
            })
        
        return jsonify({'disponible': True, 'message': 'Cr�neau disponible'})
        
    except (OperationalError, ProgrammingError):
        return jsonify({'disponible': True, 'message': 'V�rification non disponible'})
    except Exception as e:
        return jsonify({'disponible': False, 'message': f'Erreur: {str(e)}'}), 500

@reservations_bp.route('/generation')
@login_required
def generation():
    """Page de g�n�ration d'emploi du temps (Admin uniquement)"""
    if current_user.role != 'administrateur':
        flash('Acc�s refus�. R�serv� aux administrateurs.', 'error')
        return redirect(url_for('reservations.planning'))
    
    # Fili�res HESTIM
    filieres = [
        # P�le Ing�nierie
        "G�nie Industriel et Logistique",
        "G�nie Civil",
        "Ing�nierie Informatique",
        
        # P�le Management
        "Management des Entreprises et des Organisations",
        "Gestion internationale et logistique",
        "Assurance, Banque, Finance",
        "Gestion de PME � PMI",
        "Achats Logistique et Transport",
        "Marketing et Commerce International",
        "Marketing et Transformation Digitale",
        "Achats et Supply Chain Management",
        "Finance, Audit et Contr�le",
        "Gestion des Ressources Humaines"
    ]
    
    return render_template('reservations/generation.html', filieres=filieres)

@reservations_bp.route('/api/generer-emploi-du-temps', methods=['POST'])
@login_required
def generer_emploi_du_temps():
    if current_user.role != 'administrateur':
        return jsonify({'ok': False, 'message': 'Acc�s refus�'}), 403

    data = request.get_json(silent=True) or {}

    today = date.today()
    start_default = today + timedelta(days=(7 - today.weekday()) % 7)
    if start_default == today and today.weekday() != 0:
        start_default = today + timedelta(days=7)
    end_default = start_default + timedelta(days=6)

    try:
        start_date = _parse_iso_date(data.get('date_debut'), start_default)
        end_date = _parse_iso_date(data.get('date_fin'), end_default)
    except ValueError:
        return jsonify({'ok': False, 'message': 'Format de date invalide (attendu YYYY-MM-DD)'}), 400

    if end_date < start_date:
        return jsonify({'ok': False, 'message': 'date_fin doit �tre >= date_debut'}), 400

    include_weekends = bool(data.get('inclure_weekend', False))
    include_samedi = bool(data.get('inclure_samedi', True))
    include_dimanche = bool(data.get('inclure_dimanche', False))
    if include_weekends:
        include_samedi = True
        include_dimanche = True
    groupe_id = data.get('id_groupe')
    filiere = data.get('filiere')
    semestre = data.get('semestre')
    dry_run = bool(data.get('dry_run', False))
    forcer_disponibilites = bool(data.get('forcer_disponibilites', False))
    try:
        seances_par_semaine = int(data.get('seances_par_semaine', 1))
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'message': 'seances_par_semaine doit �tre un entier'}), 400

    if seances_par_semaine < 0:
        return jsonify({'ok': False, 'message': 'seances_par_semaine doit �tre >= 0'}), 400
    if seances_par_semaine > 10:
        seances_par_semaine = 10

    slots = [
        (time_obj(9, 0), time_obj(11, 0)),
        (time_obj(11, 0), time_obj(13, 0)),
        (time_obj(14, 0), time_obj(16, 0)),
        (time_obj(16, 0), time_obj(18, 0)),
    ]
    heures_par_seance = 2

    try:
        cours_query = Cours.query.options(joinedload(Cours.groupe), joinedload(Cours.professeur))
        if groupe_id is not None and str(groupe_id).strip() != '':
            cours_query = cours_query.filter(Cours.id_groupe == int(groupe_id))
        if semestre is not None and str(semestre).strip() != '':
            cours_query = cours_query.filter(Cours.semestre == int(semestre))
        if filiere is not None and str(filiere).strip() != '':
            from models import Groupe
            cours_query = cours_query.join(Groupe).filter(Groupe.filiere == filiere)

        cours_list = cours_query.order_by(Cours.id_groupe, Cours.code_cours).all()
        salles = Salle.query.filter_by(statut='disponible').order_by(Salle.capacite.asc()).all()
    except (OperationalError, ProgrammingError):
        return jsonify({'ok': False, 'message': 'Base de donn�es non initialis�e'}), 500
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'message': 'Param�tres invalides (id_groupe/semestre)'}), 400

    if not cours_list:
        return jsonify({
            'ok': True,
            'message': 'Aucun cours � planifier avec ces filtres',
            'date_debut': start_date.isoformat(),
            'date_fin': end_date.isoformat(),
            'created': 0,
            'unscheduled': [],
        })

    candidate_slots = []
    for d in _daterange(start_date, end_date):
        if d.weekday() == 5 and not include_samedi:
            continue
        if d.weekday() == 6 and not include_dimanche:
            continue
        for h_debut, h_fin in slots:
            candidate_slots.append((d, h_debut, h_fin))

    if not candidate_slots:
        return jsonify({'ok': False, 'message': 'Aucun cr�neau candidat dans la p�riode demand�e'}), 400
    
    nb_semaines = max(1, ((end_date - start_date).days + 1 + 6) // 7)

    occupied_salle = set()
    occupied_prof = set()
    occupied_groupe = set()

    professeur_ids = {c.id_professeur for c in cours_list}
    disponibilites_cache = _build_disponibilites_cache(professeur_ids)
    has_any_disponibilite = False
    if disponibilites_cache is not None:
        for v in disponibilites_cache.values():
            if v:
                has_any_disponibilite = True
                break

    try:
        existing = (
            Reservation.query
            .join(Creneau)
            .join(Cours)
            .filter(
                Reservation.statut == 'confirmee',
                Creneau.jour >= start_date,
                Creneau.jour <= end_date,
            )
            .with_entities(
                Reservation.id_salle,
                Creneau.jour,
                Creneau.heure_debut,
                Creneau.heure_fin,
                Cours.id_professeur,
                Cours.id_groupe,
            )
            .all()
        )
        for id_salle, jour, heure_debut, heure_fin, id_professeur, id_groupe in existing:
            slot_key = (jour, heure_debut, heure_fin)
            occupied_salle.add((id_salle, slot_key))
            occupied_prof.add((id_professeur, slot_key))
            occupied_groupe.add((id_groupe, slot_key))
    except (OperationalError, ProgrammingError):
        pass

    creneau_cache = {}

    created = 0
    scheduled_by_course = {}
    unscheduled = []

    try:
        for cours in cours_list:
            effectif = getattr(cours.groupe, 'effectif', None) or 0
            if effectif <= 0:
                unscheduled.append({
                    'id_cours': cours.id_cours,
                    'code_cours': cours.code_cours,
                    'message': 'Groupe sans effectif',
                })
                continue

            salles_eligibles = [s for s in salles if s.capacite >= effectif]
            if not salles_eligibles:
                unscheduled.append({
                    'id_cours': cours.id_cours,
                    'code_cours': cours.code_cours,
                    'message': 'Aucune salle assez grande',
                })
                continue

            salles_eligibles.sort(key=lambda s: _salle_rank_for_cours(s, cours, effectif))

            total_heures = int(cours.nombre_heures or 0)
            if total_heures <= 0:
                continue

            seances_voulues_total = (total_heures + heures_par_seance - 1) // heures_par_seance
            seances_voulues = min(seances_voulues_total, nb_semaines * seances_par_semaine)
            if seances_voulues <= 0:
                continue
            seances_planifiees = 0

            start_index = cours.id_cours % len(candidate_slots)
            for i in range(len(candidate_slots)):
                if seances_planifiees >= seances_voulues:
                    break

                d, h_debut, h_fin = candidate_slots[(start_index + i) % len(candidate_slots)]
                slot_key = (d, h_debut, h_fin)

                if (cours.id_professeur, slot_key) in occupied_prof:
                    continue
                if (cours.id_groupe, slot_key) in occupied_groupe:
                    continue
                if not _professeur_est_disponible(
                    cours.id_professeur,
                    d,
                    h_debut,
                    h_fin,
                    disponibilites_cache=disponibilites_cache,
                    forcer_disponibilites=forcer_disponibilites and has_any_disponibilite,
                ):
                    continue

                chosen_salle = None
                for s in salles_eligibles:
                    if (s.id_salle, slot_key) in occupied_salle:
                        continue
                    chosen_salle = s
                    break

                if not chosen_salle:
                    continue

                if dry_run:
                    occupied_salle.add((chosen_salle.id_salle, slot_key))
                    occupied_prof.add((cours.id_professeur, slot_key))
                    occupied_groupe.add((cours.id_groupe, slot_key))
                    created += 1
                    seances_planifiees += 1
                    continue

                creneau = creneau_cache.get(slot_key)
                if not creneau:
                    creneau = Creneau.query.filter_by(jour=d, heure_debut=h_debut, heure_fin=h_fin).first()
                    if not creneau:
                        creneau = Creneau(
                            jour=d,
                            heure_debut=h_debut,
                            heure_fin=h_fin,
                            periode=_periode_from_heure_debut(h_debut),
                        )
                        db.session.add(creneau)
                        db.session.flush()
                    creneau_cache[slot_key] = creneau

                reservation = Reservation(
                    id_cours=cours.id_cours,
                    id_salle=chosen_salle.id_salle,
                    id_creneau=creneau.id_creneau,
                    id_utilisateur=current_user.id_utilisateur,
                    statut='confirmee',
                    commentaire='G�n�r� automatiquement',
                )
                db.session.add(reservation)
                db.session.flush()

                occupied_salle.add((chosen_salle.id_salle, slot_key))
                occupied_prof.add((cours.id_professeur, slot_key))
                occupied_groupe.add((cours.id_groupe, slot_key))

                created += 1
                seances_planifiees += 1

            scheduled_by_course[cours.id_cours] = seances_planifiees
            if seances_planifiees < seances_voulues:
                unscheduled.append({
                    'id_cours': cours.id_cours,
                    'code_cours': cours.code_cours,
                    'seances_voulues': seances_voulues,
                    'seances_planifiees': seances_planifiees,
                    'message': 'Pas assez de cr�neaux disponibles sans conflit',
                })

        if not dry_run:
            db.session.commit()

        return jsonify({
            'ok': True,
            'date_debut': start_date.isoformat(),
            'date_fin': end_date.isoformat(),
            'dry_run': dry_run,
            'inclure_samedi': include_samedi,
            'inclure_dimanche': include_dimanche,
            'seances_par_semaine': seances_par_semaine,
            'nb_semaines': nb_semaines,
            'forcer_disponibilites': forcer_disponibilites,
            'created': created,
            'unscheduled': unscheduled,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'message': f'Erreur: {str(e)}'}), 500

@reservations_bp.route('/<int:id>')
@login_required
def detail(id):
    """D�tails d'une r�servation"""
    try:
        reservation = Reservation.query.options(
            joinedload(Reservation.creneau),
            joinedload(Reservation.cours).joinedload(Cours.professeur),
            joinedload(Reservation.cours).joinedload(Cours.groupe),
            joinedload(Reservation.salle)
        ).get_or_404(id)
        
        # V�rifier les permissions
        if current_user.role == 'enseignant':
            from models import Professeur
            professeur = Professeur.query.filter_by(email=current_user.email).first()
            if professeur and reservation.cours.id_professeur != professeur.id_professeur:
                flash('Vous n\'avez pas acc�s � cette r�servation', 'error')
                return redirect(url_for('reservations.liste'))
        
        conflits = reservation.verifier_conflits()
        
        return render_template('reservations/detail.html', reservation=reservation, conflits=conflits)
    except (OperationalError, ProgrammingError):
        flash('Erreur lors du chargement de la r�servation', 'error')
        return redirect(url_for('reservations.liste'))

@reservations_bp.route('/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(id):
    """Modifier une r�servation"""
    try:
        reservation = Reservation.query.options(
            joinedload(Reservation.creneau),
            joinedload(Reservation.cours).joinedload(Cours.groupe)
        ).get_or_404(id)
        
        if request.method == 'POST':
            id_salle = request.form.get('id_salle')
            jour = request.form.get('jour')
            heure_debut = request.form.get('heure_debut')
            heure_fin = request.form.get('heure_fin')
            commentaire = request.form.get('commentaire', '').strip()
            
            if not all([id_salle, jour, heure_debut, heure_fin]):
                flash('Veuillez remplir tous les champs obligatoires', 'error')
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/modifier.html', reservation=reservation, salles_list=salles_list)
            
            # V�rifier la capacit�
            salle = Salle.query.get(id_salle)
            if salle.capacite < reservation.cours.groupe.effectif:
                flash(f'La capacit� de la salle est insuffisante', 'error')
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/modifier.html', reservation=reservation, salles_list=salles_list)
            
            # Cr�er ou trouver le cr�neau
            jour_date = datetime.strptime(jour, '%Y-%m-%d').date()
            heure_debut_time = datetime.strptime(heure_debut, '%H:%M').time()
            heure_fin_time = datetime.strptime(heure_fin, '%H:%M').time()
            
            if heure_debut_time < time_obj(12, 0):
                periode = 'matin'
            elif heure_debut_time < time_obj(18, 0):
                periode = 'apres-midi'
            else:
                periode = 'soir'
            
            creneau = Creneau.query.filter_by(
                jour=jour_date,
                heure_debut=heure_debut_time,
                heure_fin=heure_fin_time
            ).first()
            
            if not creneau:
                creneau = Creneau(
                    jour=jour_date,
                    heure_debut=heure_debut_time,
                    heure_fin=heure_fin_time,
                    periode=periode
                )
                db.session.add(creneau)
                db.session.flush()
            
            # Vrifier les conflits (en excluant la rservation actuelle)
            conflits = []
            
            # Conflit Salle
            conflit_salle = Reservation.query.filter(
                Reservation.id_salle == id_salle,
                Reservation.id_creneau == creneau.id_creneau,
                Reservation.statut == 'confirmee',
                Reservation.id_reservation != id
            ).first()
            if conflit_salle:
                conflits.append('la salle est déjà réservée pour ce créneau')

            # Conflit Professeur
            conflit_prof = Reservation.query.join(Cours).filter(
                Cours.id_professeur == reservation.cours.id_professeur,
                Reservation.id_creneau == creneau.id_creneau,
                Reservation.statut == 'confirmee',
                Reservation.id_reservation != id
            ).first()
            if conflit_prof:
                conflits.append('le professeur a déjà un cours à ce créneau')

            # Conflit Groupe
            conflit_groupe = Reservation.query.join(Cours).filter(
                Cours.id_groupe == reservation.cours.id_groupe,
                Reservation.id_creneau == creneau.id_creneau,
                Reservation.statut == 'confirmee',
                Reservation.id_reservation != id
            ).first()
            if conflit_groupe:
                conflits.append('le groupe a déjà un cours à ce créneau')
            
            if conflits:
                flash('Conflit détecté: ' + ', '.join(conflits), 'error')
                salles_list = Salle.query.filter_by(statut='disponible').all()
                return render_template('reservations/modifier.html', reservation=reservation, salles_list=salles_list)
            
            # Mettre  jour
            reservation.id_salle = id_salle
            reservation.id_creneau = creneau.id_creneau
            reservation.commentaire = commentaire
            reservation.modifie_le = datetime.utcnow()
            
            db.session.commit()
            
            # Notification
            try:
                msg_notif = f'Réservation reportée/modifiée pour le cours {reservation.cours.nom_cours}. Nouveau créneau: {jour_date.strftime("%d/%m/%Y")} à {heure_debut_time.strftime("%H:%M")}.'
                notification = Notification(
                    id_utilisateur=current_user.id_utilisateur,
                    type_notification='modification',
                    message=msg_notif,
                    id_reservation=reservation.id_reservation
                )
                db.session.add(notification)
                db.session.commit()
                
                # Envoi Email
                email_dest = reservation.cours.professeur.email if reservation.cours.professeur else "etudiants@hestim.ma"
                envoyer_email_notification(
                    destinataire=email_dest,
                    sujet="[Hestim Schedule] Report de cours",
                    corps=msg_notif
                )
                
            except (OperationalError, ProgrammingError):
                pass
            
            flash('Réservation reportée avec succès ! Email de notification envoyé.', 'success')
            return redirect(url_for('reservations.detail', id=id))
        
        # GET: Afficher le formulaire
        salles_list = Salle.query.filter_by(statut='disponible').all()
        return render_template('reservations/modifier.html', reservation=reservation, salles_list=salles_list)
    except (OperationalError, ProgrammingError):
        flash('Erreur lors du chargement de la rservation', 'error')
        return redirect(url_for('reservations.liste'))
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('reservations.liste'))

@reservations_bp.route('/<int:id>/annuler', methods=['POST'])
@login_required
def annuler(id):
    """Annuler une rservation"""
    try:
        reservation = Reservation.query.get_or_404(id)
        
        reservation.statut = 'annulee'
        reservation.modifie_le = datetime.utcnow()
        
        db.session.commit()
        
        # Notification
        try:
            msg_notif = f'Réservation annulée pour le cours {reservation.cours.nom_cours}.'
            notification = Notification(
                id_utilisateur=current_user.id_utilisateur,
                type_notification='annulation',
                message=msg_notif,
                id_reservation=reservation.id_reservation
            )
            db.session.add(notification)
            db.session.commit()
            
            # Envoi Email
            email_dest = reservation.cours.professeur.email if reservation.cours.professeur else "etudiants@hestim.ma"
            envoyer_email_notification(
                destinataire=email_dest,
                sujet="[Hestim Schedule] Annulation de cours",
                corps=msg_notif
            )
        except (OperationalError, ProgrammingError):
            pass
        
        flash('Réservation annulée avec succès. Email de notification envoyé.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'annulation: {str(e)}', 'error')
    
    return redirect(url_for('reservations.liste'))

