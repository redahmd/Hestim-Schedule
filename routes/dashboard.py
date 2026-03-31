from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import Reservation, Cours, Salle, Creneau, Groupe, Professeur, Etudiant
from database import db
from datetime import datetime, date, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import func, distinct, case
import json

try:
    from data_analysis import compute_admin_kpis, compute_prof_kpis
except ImportError:
    pass

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/home')
@login_required
def home():
    """Tableau de bord principal"""
    # Statistiques selon le rôle
    stats = {}
    reservations_prochaines = []
    
    try:
        if current_user.role == 'administrateur':
            stats['total_reservations'] = Reservation.query.filter_by(statut='confirmee').count()
            stats['total_salles'] = Salle.query.count()
            stats['total_cours'] = Cours.query.count()
            stats['reservations_aujourdhui'] = Reservation.query.join(Creneau).filter(
                Creneau.jour == date.today(),
                Reservation.statut == 'confirmee'
            ).count()
            
            # Réservations à venir (7 prochains jours)
            date_fin = date.today() + timedelta(days=7)
            reservations_prochaines = Reservation.query.options(
                joinedload(Reservation.creneau),
                joinedload(Reservation.cours).joinedload(Cours.professeur),
                joinedload(Reservation.cours).joinedload(Cours.groupe),
                joinedload(Reservation.salle)
            ).join(Creneau).filter(
                Creneau.jour >= date.today(),
                Creneau.jour <= date_fin,
                Reservation.statut == 'confirmee'
            ).order_by(Creneau.jour, Creneau.heure_debut).limit(10).all()

            # Data Science KPIs for Admin Home
            try:
                kpis = compute_admin_kpis()
                stats['taux_conflits'] = kpis.get('taux_conflits', 0)
                stats['taux_modifs'] = kpis.get('taux_modifs', 0)
                stats['moy_heures_prof'] = kpis.get('moy_heures_prof', 0)
                stats['moy_heures_etu'] = kpis.get('moy_heures_etu', 0)
                stats['taux_absence'] = kpis.get('taux_absence', 0)
            except Exception as e:
                print("Erreur chargement KPIs admin:", e)
        
        elif current_user.role == 'enseignant':
            # Trouver le professeur associé
            from models import Professeur
            professeur = Professeur.query.filter_by(email=current_user.email).first()
            
            if professeur:
                stats['mes_cours'] = Cours.query.filter_by(id_professeur=professeur.id_professeur).count()
                stats['mes_reservations'] = Reservation.query.join(Cours).filter(
                    Cours.id_professeur == professeur.id_professeur,
                    Reservation.statut == 'confirmee'
                ).count()
                
                # Prochaines réservations
                reservations_prochaines = Reservation.query.options(
                    joinedload(Reservation.creneau),
                    joinedload(Reservation.cours).joinedload(Cours.professeur),
                    joinedload(Reservation.cours).joinedload(Cours.groupe),
                    joinedload(Reservation.salle)
                ).join(Cours).join(Creneau).filter(
                    Cours.id_professeur == professeur.id_professeur,
                    Creneau.jour >= date.today(),
                    Reservation.statut == 'confirmee'
                ).order_by(Creneau.jour, Creneau.heure_debut).limit(10).all()
        
        else:  # étudiant
            from models import Etudiant, Groupe
            etudiant = Etudiant.query.filter_by(email=current_user.email).first()
            
            # Initialiser les stats par défaut
            stats['reservations_groupe'] = 0
            stats['etudiant_trouve'] = etudiant is not None
            stats['a_groupe'] = False
            
            if etudiant and etudiant.id_groupe:
                stats['a_groupe'] = True
                # Réservations du groupe
                stats['reservations_groupe'] = Reservation.query.join(Cours).join(Creneau).filter(
                    Cours.id_groupe == etudiant.id_groupe,
                    Creneau.jour >= date.today(),
                    Reservation.statut == 'confirmee'
                ).count()
                
                reservations_prochaines = Reservation.query.options(
                    joinedload(Reservation.creneau),
                    joinedload(Reservation.cours).joinedload(Cours.professeur),
                    joinedload(Reservation.cours).joinedload(Cours.groupe),
                    joinedload(Reservation.salle)
                ).join(Cours).join(Creneau).filter(
                    Cours.id_groupe == etudiant.id_groupe,
                    Creneau.jour >= date.today(),
                    Reservation.statut == 'confirmee'
                ).order_by(Creneau.jour, Creneau.heure_debut).limit(10).all()
    
    except Exception as e:
        # En cas d'erreur, initialiser avec des valeurs par défaut
        if current_user.role == 'administrateur':
            stats = {
                'total_reservations': 0,
                'total_salles': 0,
                'total_cours': 0,
                'reservations_aujourdhui': 0
            }
        elif current_user.role == 'enseignant':
            stats = {
                'mes_cours': 0,
                'mes_reservations': 0
            }
        else:
            stats = {
                'reservations_groupe': 0,
                'a_groupe': False
            }
        reservations_prochaines = []
    
    return render_template('dashboard/home.html', stats=stats, reservations_prochaines=reservations_prochaines)


@dashboard_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Page de profil utilisateur"""
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(old_password):
            flash('Ancien mot de passe incorrect.', 'error')
        elif new_password != confirm_password:
            flash('Les nouveaux mots de passe ne correspondent pas.', 'error')
        elif len(new_password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'error')
        else:
            try:
                current_user.set_password(new_password)
                from database import db
                db.session.commit()
                flash('Mot de passe mis à jour avec succès.', 'success')
            except Exception as e:
                flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
            
    user_details = {}
    
    try:
        if current_user.role == 'enseignant':
            from models import Professeur
            prof = Professeur.query.filter_by(email=current_user.email).first()
            if prof:
                user_details = {
                    'Département': prof.departement,
                    'Spécialité': prof.specialite,
                    'Téléphone': prof.telephone,
                    'Statut': 'Actif' if prof.actif else 'Inactif'
                }
                
        elif current_user.role == 'etudiant':
            from models import Etudiant
            etu = Etudiant.query.filter_by(email=current_user.email).first()
            if etu:
                user_details = {
                    'Niveau': etu.niveau,
                    'Groupe': etu.groupe.nom_groupe if etu.groupe else 'Non assigné',
                    'Date d\'inscription': etu.date_inscription.strftime('%d/%m/%Y') if etu.date_inscription else '-',
                    'Statut': 'Actif' if etu.actif else 'Inactif'
                }
                
        elif current_user.role == 'administrateur':
            user_details = {
                'Statut': 'Administrateur Système',
                'Accès': 'Complet'
            }
            
    except Exception as e:
        print(f"Erreur recuperation profil: {e}")
        
    return render_template('dashboard/profile.html', user_details=user_details)

@dashboard_bp.route('/validate_planning', methods=['POST'])
@login_required
def validate_planning():
    """Valide toutes les réservations en attente"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard.home'))
    
    try:
        from database import db
        # Mettre à jour toutes les réservations en attente -> confirmee
        count = Reservation.query.filter_by(statut='en_attente').update({Reservation.statut: 'confirmee'})
        db.session.commit()
        
        if count > 0:
            flash(f'{count} réservations ont été validées et publiées avec succès !', 'success')
        else:
            flash('Aucune réservation en attente de validation.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la validation : {str(e)}', 'error')
        
    return redirect(url_for('dashboard.home'))

@dashboard_bp.route('/statistics')
@login_required
def statistics():
    """Page de statistiques avancées pour l'administrateur"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard.home'))

    stats = {}
    
    try:
        # 1. Nombre total de cours assignés (distinct courses in reservations)
        stats['total_cours_assignes'] = db.session.query(func.count(distinct(Reservation.id_cours)))\
            .filter(Reservation.statut == 'confirmee').scalar()
            
        # 2. Nombre total d’heures de cours par semaine
        # On regarde la semaine courante
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        
        # Calculer la durée des créneaux pour les réservations de la semaine
        reservations_semaine = Reservation.query.join(Creneau).filter(
            Creneau.jour >= start_week,
            Creneau.jour <= end_week,
            Reservation.statut == 'confirmee'
        ).all()
        
        total_minutes = 0
        for res in reservations_semaine:
            # Calculer la différence entre heure_fin et heure_debut
            # Note: heure_debut/fin sont des objets time, on doit les convertir pour soustraire
            debut = datetime.combine(date.min, res.creneau.heure_debut)
            fin = datetime.combine(date.min, res.creneau.heure_fin)
            duree = (fin - debut).total_seconds() / 60
            total_minutes += duree
            
        stats['total_heures_semaine'] = round(total_minutes / 60, 1)

        # 3. Taux d’occupation (pourcentage du temps de travail)
        # Supposons 8h-18h (10h) * 6 jours (Lundi-Samedi) * Nombre de salles
        nb_salles = Salle.query.count()
        heures_ouvrables_semaine = 10 * 6 * nb_salles
        
        if heures_ouvrables_semaine > 0:
            stats['taux_occupation'] = round((stats['total_heures_semaine'] / heures_ouvrables_semaine) * 100, 1)
        else:
            stats['taux_occupation'] = 0

        # 4. Nombre d’étudiants touchés (total des effectifs des groupes uniques ayant des cours)
        # On récupère d'abord les ID des groupes concernés par les réservations de la semaine
        groupes_concernes = db.session.query(distinct(Groupe.id_groupe))\
            .join(Cours, Cours.id_groupe == Groupe.id_groupe)\
            .join(Reservation, Reservation.id_cours == Cours.id_cours)\
            .join(Creneau, Reservation.id_creneau == Creneau.id_creneau)\
            .filter(
                Reservation.statut == 'confirmee',
                Creneau.jour >= start_week,
                Creneau.jour <= end_week
            ).all()
            
        ids_groupes = [g[0] for g in groupes_concernes]
        
        if ids_groupes:
            stats['etudiants_touches'] = db.session.query(func.sum(Groupe.effectif))\
                .filter(Groupe.id_groupe.in_(ids_groupes)).scalar() or 0
        else:
            stats['etudiants_touches'] = 0

        # 5. Graphique de répartition des heures par jour de la semaine
        # On prépare les données pour Chart.js
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        heures_par_jour = {i: 0 for i in range(6)} # 0=Lundi, 5=Samedi
        
        for res in reservations_semaine:
            jour_index = res.creneau.jour.weekday()
            if 0 <= jour_index <= 5:
                debut = datetime.combine(date.min, res.creneau.heure_debut)
                fin = datetime.combine(date.min, res.creneau.heure_fin)
                duree_heures = (fin - debut).total_seconds() / 3600
                heures_par_jour[jour_index] += duree_heures
        
        stats['graph_labels'] = jours
        stats['graph_data'] = [round(heures_par_jour[i], 1) for i in range(6)]
        
        # --- NEW KPIs ---
        # KPI 1: Taux d'occupation par salle
        toutes_salles = Salle.query.all()
        heures_ouvrables_par_salle = 10 * 6  # 60 heures (10h/jour * 6 jours)
        
        taux_occupation_salle = []
        for salle in toutes_salles:
            res_salle = [r for r in reservations_semaine if r.id_salle == salle.id_salle]
            tot_minutes = 0
            for r in res_salle:
                d = datetime.combine(date.min, r.creneau.heure_debut)
                f = datetime.combine(date.min, r.creneau.heure_fin)
                tot_minutes += (f - d).total_seconds() / 60
            
            heures = tot_minutes / 60
            taux = round((heures / heures_ouvrables_par_salle) * 100, 2) if heures_ouvrables_par_salle > 0 else 0
            taux_occupation_salle.append({'salle': salle.numero_salle, 'taux': taux})
            
        taux_occupation_salle.sort(key=lambda x: x['taux'], reverse=True)
        stats['taux_occupation_salle_labels'] = [x['salle'] for x in taux_occupation_salle]
        stats['taux_occupation_salle_data'] = [x['taux'] for x in taux_occupation_salle]

        # ALL reservations for global KPIs
        all_reservations = Reservation.query.filter_by(statut='confirmee').all()

        # KPI 2: Répartition des réservations par type de salle
        repartition_salle = {}
        for res in all_reservations:
            t = res.salle.type_salle
            repartition_salle[t] = repartition_salle.get(t, 0) + 1
            
        sorted_types = sorted(repartition_salle.items(), key=lambda x: x[1], reverse=True)
        stats['repartition_type_salle_labels'] = [x[0] for x in sorted_types]
        stats['repartition_type_salle_data'] = [x[1] for x in sorted_types]
        
        # KPI 3: Nombre de réservations par professeur
        repartition_prof = {}
        for res in all_reservations:
            prof_nom = f"{res.cours.professeur.nom} {res.cours.professeur.prenom}"
            repartition_prof[prof_nom] = repartition_prof.get(prof_nom, 0) + 1
            
        sorted_profs = sorted(repartition_prof.items(), key=lambda x: x[1], reverse=True)
        stats['reservations_prof_labels'] = [x[0] for x in sorted_profs]
        stats['reservations_prof_data'] = [x[1] for x in sorted_profs]
        
        # KPI 4: Périodes de surcharge (par jour)
        res_par_jour = {}
        for res in all_reservations:
            jour_str = res.creneau.jour.strftime('%Y-%m-%d')
            res_par_jour[jour_str] = res_par_jour.get(jour_str, 0) + 1
            
        sorted_jours = sorted(res_par_jour.items(), key=lambda x: x[0])
        stats['surcharge_labels'] = [x[0] for x in sorted_jours]
        stats['surcharge_data'] = [x[1] for x in sorted_jours]
        if stats['surcharge_data']:
            stats['surcharge_moyenne'] = sum(stats['surcharge_data']) / len(stats['surcharge_data'])
        else:
            stats['surcharge_moyenne'] = 0
        # --- END NEW KPIs ---

        # --- HEATMAP: Occupation par Jour x Créneau Horaire ---
        # Créneaux représentatifs (on arrondit à l'heure)
        heatmap_jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        heatmap_creneaux = ['08h', '09h', '10h', '11h', '12h', '13h', '14h', '15h', '16h', '17h']
        
        # grille [jour_idx][creneau_idx] = nb salles occupées
        heatmap_grid = [[0] * len(heatmap_creneaux) for _ in range(len(heatmap_jours))]
        
        for res in all_reservations:
            jour_idx = res.creneau.jour.weekday()  # 0=Lundi
            if 0 <= jour_idx <= 5:
                heure_debut = res.creneau.heure_debut.hour
                heure_fin = res.creneau.heure_fin.hour
                for h in range(heure_debut, heure_fin):
                    if 8 <= h <= 17:
                        cr_idx = h - 8
                        heatmap_grid[jour_idx][cr_idx] += 1
        
        stats['heatmap_jours'] = heatmap_jours
        stats['heatmap_creneaux'] = heatmap_creneaux
        stats['heatmap_grid'] = heatmap_grid

        # --- MATRICE DE CORRELATION: Type de Salle x Jour de la Semaine ---
        # On récupère tous les types de salles distincts
        jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        types_salles_distincts = sorted(list(set(res.salle.type_salle for res in all_reservations if res.salle and res.salle.type_salle)))
        
        # matrice[type_idx][jour_idx] = nb réservations
        correlation_matrix = []
        for type_s in types_salles_distincts:
            row = [0] * 6
            for res in all_reservations:
                if res.salle and res.salle.type_salle == type_s:
                    jour_idx = res.creneau.jour.weekday()
                    if 0 <= jour_idx <= 5:
                        row[jour_idx] += 1
            correlation_matrix.append(row)
        
        stats['correlation_types'] = types_salles_distincts
        stats['correlation_jours'] = jours_semaine
        stats['correlation_matrix'] = correlation_matrix
        
        # --- MISSING DASHBOARD KPIs (PANDAS/NUMPY/SCIPY) ---
        try:
            kpis = compute_admin_kpis()
            stats['moy_heures_prof'] = kpis.get('moy_heures_prof', 0)
            stats['moy_heures_etu'] = kpis.get('moy_heures_etu', 0)
            stats['taux_absence'] = kpis.get('taux_absence', 0)
            stats['taux_conflits'] = kpis.get('taux_conflits', 0)
            stats['taux_modifs'] = kpis.get('taux_modifs', 0)
            stats['heures_pleines'] = kpis.get('heures_pleines', [])
            stats['heatmap_b64'] = kpis.get('heatmap_b64')
            stats['corr_b64'] = kpis.get('corr_b64')
            stats['donut_b64'] = kpis.get('donut_b64')
        except Exception as ds_e:
            print(f"Erreur KPIs datascientist: {str(ds_e)}")
            
    except Exception as e:
        print(f"Erreur calcul statistiques: {str(e)}")
        flash(f"Erreur lors du calcul des statistiques: {str(e)}", "error")
        stats = {
            'total_cours_assignes': 0,
            'total_heures_semaine': 0,
            'taux_occupation': 0,
            'etudiants_touches': 0,
            'graph_labels': [],
            'graph_data': [],
            'liste_cours': [],
            'taux_occupation_salle_labels': [],
            'taux_occupation_salle_data': [],
            'repartition_type_salle_labels': [],
            'repartition_type_salle_data': [],
            'reservations_prof_labels': [],
            'reservations_prof_data': [],
            'surcharge_labels': [],
            'surcharge_data': [],
            'surcharge_moyenne': 0,
            'heatmap_jours': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'],
            'heatmap_creneaux': ['08h', '09h', '10h', '11h', '12h', '13h', '14h', '15h', '16h', '17h'],
            'heatmap_grid': [[0]*10 for _ in range(6)],
            'correlation_types': [],
            'correlation_jours': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'],
            'correlation_matrix': [],
            'moy_heures_prof': 0,
            'moy_heures_etu': 0,
            'taux_absence': 0,
            'taux_conflits': 0,
            'taux_modifs': 0,
            'heures_pleines': [],
            'heatmap_b64': None,
            'corr_b64': None,
            'donut_b64': None
        }

    return render_template('dashboard/statistics.html', stats=stats)


@dashboard_bp.route('/export_stats')
@login_required
def export_stats():
    """Exporting KPI Data to Excel (Pandas)"""
    from flask import send_file, flash, redirect, url_for
    import pandas as pd
    import io
    
    try:
        if current_user.role != 'administrateur':
            flash('Accès refusé. Réservé aux administrateurs.', 'error')
            return redirect(url_for('dashboard.home'))
            
        from data_analysis import get_base_dataframes, compute_admin_kpis
        dfs = get_base_dataframes()
        df = dfs['full']
        
        # Format the exported data intelligently
        export_df = df.copy()
        if not export_df.empty:
            export_df = export_df[['nom_cours', 'type_cours', 'jour', 'heure_debut', 'heure_fin', 'statut']]
            
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, sheet_name='Reservations', index=False)
            
            kpis = compute_admin_kpis()
            kpi_data = [
                {'Indicateur': 'Moyenne Heures / Prof', 'Valeur': str(kpis.get('moy_heures_prof', 0)) + ' h'},
                {'Indicateur': 'Moyenne Heures / Etudiant', 'Valeur': str(kpis.get('moy_heures_etu', 0)) + ' h'},
                {'Indicateur': 'Taux Absence (Simulation)', 'Valeur': str(kpis.get('taux_absence', 0)) + ' %'},
                {'Indicateur': 'Taux de Conflits', 'Valeur': str(kpis.get('taux_conflits', 0)) + ' %'},
                {'Indicateur': 'Modifications', 'Valeur': str(kpis.get('taux_modifs', 0)) + ' %'}
            ]
            kpi_df = pd.DataFrame(kpi_data)
            kpi_df.to_excel(writer, sheet_name='KPIs Avances', index=False)
            
        output.seek(0)
        return send_file(output, download_name='rapport_statistiques.xlsx', as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        print(f"Erreur export Excel: {e}")
        from flask import flash, redirect, url_for
        flash('Erreur lors de la génération du fichier Excel. Vérifiez les dépendances.', 'error')
        return redirect(url_for('dashboard.statistics'))

@dashboard_bp.route('/mes_statistiques')
@login_required
def mes_statistiques():
    """Page de statistiques pour le professeur connecté"""
    if current_user.role != 'enseignant':
        flash('Accès refusé. Cette page est réservée aux enseignants.', 'error')
        return redirect(url_for('dashboard.home'))

    from models import Professeur
    professeur = Professeur.query.filter_by(email=current_user.email).first()
    
    if not professeur:
        flash('Profil professeur introuvable.', 'error')
        return redirect(url_for('dashboard.home'))

    stats = {
        'professeur': professeur
    }
    
    try:
        # Get all confirmed reservations for this professor once
        all_reservations = Reservation.query.join(Cours).filter(
            Cours.id_professeur == professeur.id_professeur,
            Reservation.statut == 'confirmee'
        ).all()

        # 1. Nombre total de cours assignés à ce prof
        stats['total_cours_assignes'] = Cours.query.filter_by(id_professeur=professeur.id_professeur).count()
            
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        
        reservations_semaine = [r for r in all_reservations if start_week <= r.creneau.jour <= end_week]
        
        total_minutes = 0
        for res in reservations_semaine:
            debut = datetime.combine(date.min, res.creneau.heure_debut)
            fin = datetime.combine(date.min, res.creneau.heure_fin)
            duree = (fin - debut).total_seconds() / 60
            total_minutes += duree
            
        stats['total_heures_semaine'] = round(total_minutes / 60, 1)

        charge_standard = 18.0
        stats['taux_occupation'] = round((stats['total_heures_semaine'] / charge_standard) * 100, 1)

        groupes_concernes = db.session.query(distinct(Groupe.id_groupe))\
            .join(Cours, Cours.id_groupe == Groupe.id_groupe)\
            .join(Reservation, Reservation.id_cours == Cours.id_cours)\
            .join(Creneau, Reservation.id_creneau == Creneau.id_creneau)\
            .filter(
                Cours.id_professeur == professeur.id_professeur,
                Reservation.statut == 'confirmee',
                Creneau.jour >= start_week,
                Creneau.jour <= end_week
            ).all()
            
        ids_groupes = [g[0] for g in groupes_concernes]
        
        if ids_groupes:
            stats['etudiants_touches'] = db.session.query(func.sum(Groupe.effectif))\
                .filter(Groupe.id_groupe.in_(ids_groupes)).scalar() or 0
        else:
            stats['etudiants_touches'] = 0

        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        heures_par_jour = {i: 0 for i in range(6)}
        
        for res in reservations_semaine:
            jour_index = res.creneau.jour.weekday()
            if 0 <= jour_index <= 5:
                debut = datetime.combine(date.min, res.creneau.heure_debut)
                fin = datetime.combine(date.min, res.creneau.heure_fin)
                duree_heures = (fin - debut).total_seconds() / 3600
                heures_par_jour[jour_index] += duree_heures
        
        stats['graph_labels'] = jours
        stats['graph_data'] = [round(heures_par_jour[i], 1) for i in range(6)]
        
        # --- NEW KPIs PROFESSEUR: Taux d'occupation par salle (Admin-like) ---
        heures_ouvrables_par_salle = 10 * 6  # 60 heures (10h/jour * 6 jours)
        salles_utilisees = list(set(res.salle for res in all_reservations if res.salle))
        
        taux_occupation_salle = []
        for salle in salles_utilisees:
            res_salle_prof = [r for r in all_reservations if r.id_salle == salle.id_salle]
            tot_minutes = 0
            for r in res_salle_prof:
                d = datetime.combine(date.min, r.creneau.heure_debut)
                f = datetime.combine(date.min, r.creneau.heure_fin)
                tot_minutes += (f - d).total_seconds() / 60
            
            heures = tot_minutes / 60
            taux = round((heures / heures_ouvrables_par_salle) * 100, 2) if heures_ouvrables_par_salle > 0 else 0
            taux_occupation_salle.append({'salle': salle.numero_salle, 'taux': taux})
            
        taux_occupation_salle.sort(key=lambda x: x['taux'], reverse=True)
        stats['taux_occupation_salle_labels'] = [x['salle'] for x in taux_occupation_salle]
        stats['taux_occupation_salle_data'] = [x['taux'] for x in taux_occupation_salle]

        stats['liste_cours'] = []
        for res in reservations_semaine:
            stats['liste_cours'].append({
                'cours': res.cours.nom_cours,
                'code': res.cours.code_cours,
                'jour': res.creneau.jour.strftime('%d/%m/%Y'),
                'horaire': f"{res.creneau.heure_debut.strftime('%H:%M')} - {res.creneau.heure_fin.strftime('%H:%M')}",
                'salle': res.salle.numero_salle,
                'groupe': res.cours.groupe.nom_groupe
            })

        # --- RICH KPIs ---
        # KPI 2: Répartition des réservations par type de salle
        repartition_salle = {}
        for res in all_reservations:
            t = res.salle.type_salle if res.salle else 'Inconnu'
            repartition_salle[t] = repartition_salle.get(t, 0) + 1
            
        sorted_types = sorted(repartition_salle.items(), key=lambda x: x[1], reverse=True)
        stats['repartition_type_salle_labels'] = [x[0] for x in sorted_types]
        stats['repartition_type_salle_data'] = [x[1] for x in sorted_types]
        
        # KPI 4: Périodes de surcharge (par jour)
        res_par_jour = {}
        for res in all_reservations:
            jour_str = res.creneau.jour.strftime('%Y-%m-%d')
            res_par_jour[jour_str] = res_par_jour.get(jour_str, 0) + 1
            
        sorted_jours = sorted(res_par_jour.items(), key=lambda x: x[0])
        stats['surcharge_labels'] = [x[0] for x in sorted_jours]
        stats['surcharge_data'] = [x[1] for x in sorted_jours]
        if stats['surcharge_data']:
            stats['surcharge_moyenne'] = sum(stats['surcharge_data']) / len(stats['surcharge_data'])
        else:
            stats['surcharge_moyenne'] = 0

        # --- HEATMAP: Occupation par Jour x Créneau Horaire ---
        heatmap_jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        heatmap_creneaux = ['08h', '09h', '10h', '11h', '12h', '13h', '14h', '15h', '16h', '17h']
        
        heatmap_grid = [[0] * len(heatmap_creneaux) for _ in range(len(heatmap_jours))]
        for res in all_reservations:
            jour_idx = res.creneau.jour.weekday()
            if 0 <= jour_idx <= 5:
                heure_debut = res.creneau.heure_debut.hour
                heure_fin = res.creneau.heure_fin.hour
                for h in range(heure_debut, heure_fin):
                    if 8 <= h <= 17:
                        cr_idx = h - 8
                        heatmap_grid[jour_idx][cr_idx] += 1
        
        stats['heatmap_jours'] = heatmap_jours
        stats['heatmap_creneaux'] = heatmap_creneaux
        stats['heatmap_grid'] = heatmap_grid

        # --- MATRICE DE CORRELATION: Type de Salle x Jour de la Semaine ---
        jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        types_salles_distincts = sorted(list(set(res.salle.type_salle for res in all_reservations if res.salle and res.salle.type_salle)))
        
        correlation_matrix = []
        for type_s in types_salles_distincts:
            row = [0] * 6
            for res in all_reservations:
                if res.salle and res.salle.type_salle == type_s:
                    jour_idx = res.creneau.jour.weekday()
                    if 0 <= jour_idx <= 5:
                        row[jour_idx] += 1
            correlation_matrix.append(row)
        
        stats['correlation_types'] = types_salles_distincts
        stats['correlation_jours'] = jours_semaine
        stats['correlation_matrix'] = correlation_matrix
        
        try:
            prof_kpis = compute_prof_kpis(professeur.id_professeur)
            stats['prof_taux_modifs'] = prof_kpis.get('taux_modifs', 0)
            stats['prof_salles_freq'] = prof_kpis.get('salles_freq', {})
            stats['prof_pie_b64'] = prof_kpis.get('prof_pie_b64')
        except Exception as e:
            print("Erreur Data science prof:", e)
            
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"DEBUG: Erreur dans mes_statistiques: {error_msg}")
        # Log to a temporary file too just in case terminal buffer is full
        with open('debug_stats_error.log', 'a', encoding='utf-8') as f:
            f.write(f"\n--- {datetime.now()} ---\n{error_msg}\n")
            
        flash(f"Erreur lors du calcul des statistiques: {str(e)}", "error")
        stats = {
            'professeur': professeur,
            'total_cours_assignes': 0,
            'total_heures_semaine': 0,
            'taux_occupation': 0,
            'etudiants_touches': 0,
            'graph_labels': [],
            'graph_data': [],
            'liste_cours': [],
            'taux_occupation_salle_labels': [],
            'taux_occupation_salle_data': [],
            'repartition_type_salle_labels': [],
            'repartition_type_salle_data': [],
            'surcharge_labels': [],
            'surcharge_data': [],
            'surcharge_moyenne': 0,
            'heatmap_jours': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'],
            'heatmap_creneaux': ['08h', '09h', '10h', '11h', '12h', '13h', '14h', '15h', '16h', '17h'],
            'heatmap_grid': [[0]*10 for _ in range(6)],
            'correlation_types': [],
            'correlation_jours': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'],
            'correlation_matrix': []
        }

    return render_template('dashboard/mes_statistiques.html', stats=stats)


@dashboard_bp.route('/statistics/professeur/<int:id_professeur>')
@login_required
def statistics_professeur(id_professeur):
    """Page de statistiques pour un professeur spécifique (Admin)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('dashboard.home'))

    professeur = Professeur.query.get_or_404(id_professeur)
    stats = {
        'professeur': professeur
    }
    
    try:
        # Get all confirmed reservations for this professor once
        all_reservations = Reservation.query.join(Cours).filter(
            Cours.id_professeur == id_professeur,
            Reservation.statut == 'confirmee'
        ).all()

        # 1. Nombre total de cours assignés à ce prof
        stats['total_cours_assignes'] = Cours.query.filter_by(id_professeur=id_professeur).count()
            
        # 2. Nombre total d’heures de cours par semaine pour ce prof
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        
        reservations_semaine = [r for r in all_reservations if start_week <= r.creneau.jour <= end_week]
        
        total_minutes = 0
        for res in reservations_semaine:
            debut = datetime.combine(date.min, res.creneau.heure_debut)
            fin = datetime.combine(date.min, res.creneau.heure_fin)
            duree = (fin - debut).total_seconds() / 60
            total_minutes += duree
            
        stats['total_heures_semaine'] = round(total_minutes / 60, 1)

        # 3. "Taux d'occupation" ou Charge Horaire (vs 18h standard par exemple, ou juste info)
        # On va afficher le % par rapport à une charge théorique de 18h/semaine (arbitraire ou standard)
        charge_standard = 18.0
        stats['taux_occupation'] = round((stats['total_heures_semaine'] / charge_standard) * 100, 1)

        # 4. Nombre d’étudiants touchés (somme des effectifs des groupes uniques de ses cours cette semaine)
        # Groupes uniques que voir le prof cette semaine
        groupes_concernes = db.session.query(distinct(Groupe.id_groupe))\
            .join(Cours, Cours.id_groupe == Groupe.id_groupe)\
            .join(Reservation, Reservation.id_cours == Cours.id_cours)\
            .join(Creneau, Reservation.id_creneau == Creneau.id_creneau)\
            .filter(
                Cours.id_professeur == id_professeur,
                Reservation.statut == 'confirmee',
                Creneau.jour >= start_week,
                Creneau.jour <= end_week
            ).all()
            
        ids_groupes = [g[0] for g in groupes_concernes]
        
        if ids_groupes:
            stats['etudiants_touches'] = db.session.query(func.sum(Groupe.effectif))\
                .filter(Groupe.id_groupe.in_(ids_groupes)).scalar() or 0
        else:
            stats['etudiants_touches'] = 0

        # 5. Graphique de répartition des heures
        jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        heures_par_jour = {i: 0 for i in range(6)}
        
        for res in reservations_semaine:
            jour_index = res.creneau.jour.weekday()
            if 0 <= jour_index <= 5:
                debut = datetime.combine(date.min, res.creneau.heure_debut)
                fin = datetime.combine(date.min, res.creneau.heure_fin)
                duree_heures = (fin - debut).total_seconds() / 3600
                heures_par_jour[jour_index] += duree_heures
        
        stats['graph_labels'] = jours
        stats['graph_data'] = [round(heures_par_jour[i], 1) for i in range(6)]
        
        # --- NEW KPIs PROFESSEUR: Taux d'occupation par salle (Admin-like) ---
        heures_ouvrables_par_salle = 10 * 6  # 60 heures (10h/jour * 6 jours)
        salles_utilisees = list(set(res.salle for res in all_reservations if res.salle))
        
        taux_occupation_salle = []
        for salle in salles_utilisees:
            res_salle_prof = [r for r in all_reservations if r.id_salle == salle.id_salle]
            tot_minutes = 0
            for r in res_salle_prof:
                d = datetime.combine(date.min, r.creneau.heure_debut)
                f = datetime.combine(date.min, r.creneau.heure_fin)
                tot_minutes += (f - d).total_seconds() / 60
            
            heures = tot_minutes / 60
            taux = round((heures / heures_ouvrables_par_salle) * 100, 2) if heures_ouvrables_par_salle > 0 else 0
            taux_occupation_salle.append({'salle': salle.numero_salle, 'taux': taux})
            
        taux_occupation_salle.sort(key=lambda x: x['taux'], reverse=True)
        stats['taux_occupation_salle_labels'] = [x['salle'] for x in taux_occupation_salle]
        stats['taux_occupation_salle_data'] = [x['taux'] for x in taux_occupation_salle]

        # --- RICH KPIs ---
        # KPI 2: Répartition des réservations par type de salle
        repartition_salle = {}
        for res in all_reservations:
            t = res.salle.type_salle if res.salle else 'Inconnu'
            repartition_salle[t] = repartition_salle.get(t, 0) + 1
            
        sorted_types = sorted(repartition_salle.items(), key=lambda x: x[1], reverse=True)
        stats['repartition_type_salle_labels'] = [x[0] for x in sorted_types]
        stats['repartition_type_salle_data'] = [x[1] for x in sorted_types]
        
        # KPI 4: Périodes de surcharge (par jour)
        res_par_jour = {}
        for res in all_reservations:
            jour_str = res.creneau.jour.strftime('%Y-%m-%d')
            res_par_jour[jour_str] = res_par_jour.get(jour_str, 0) + 1
            
        sorted_jours = sorted(res_par_jour.items(), key=lambda x: x[0])
        stats['surcharge_labels'] = [x[0] for x in sorted_jours]
        stats['surcharge_data'] = [x[1] for x in sorted_jours]
        if stats['surcharge_data']:
            stats['surcharge_moyenne'] = sum(stats['surcharge_data']) / len(stats['surcharge_data'])
        else:
            stats['surcharge_moyenne'] = 0

        # --- HEATMAP: Occupation par Jour x Créneau Horaire ---
        heatmap_jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        heatmap_creneaux = ['08h', '09h', '10h', '11h', '12h', '13h', '14h', '15h', '16h', '17h']
        
        heatmap_grid = [[0] * len(heatmap_creneaux) for _ in range(len(heatmap_jours))]
        for res in all_reservations:
            jour_idx = res.creneau.jour.weekday()
            if 0 <= jour_idx <= 5:
                heure_debut = res.creneau.heure_debut.hour
                heure_fin = res.creneau.heure_fin.hour
                for h in range(heure_debut, heure_fin):
                    if 8 <= h <= 17:
                        cr_idx = h - 8
                        heatmap_grid[jour_idx][cr_idx] += 1
        
        stats['heatmap_jours'] = heatmap_jours
        stats['heatmap_creneaux'] = heatmap_creneaux
        stats['heatmap_grid'] = heatmap_grid

        # --- MATRICE DE CORRELATION: Type de Salle x Jour de la Semaine ---
        jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
        types_salles_distincts = sorted(list(set(res.salle.type_salle for res in all_reservations if res.salle and res.salle.type_salle)))
        
        correlation_matrix = []
        for type_s in types_salles_distincts:
            row = [0] * 6
            for res in all_reservations:
                if res.salle and res.salle.type_salle == type_s:
                    jour_idx = res.creneau.jour.weekday()
                    if 0 <= jour_idx <= 5:
                        row[jour_idx] += 1
            correlation_matrix.append(row)
        
        stats['correlation_types'] = types_salles_distincts
        stats['correlation_jours'] = jours_semaine
        stats['correlation_matrix'] = correlation_matrix
            
    except Exception as e:
        print(f"Erreur calcul statistiques prof: {str(e)}")
        flash(f"Erreur lors du calcul des statistiques: {str(e)}", "error")
        stats = {
            'professeur': professeur,
            'total_cours_assignes': 0,
            'total_heures_semaine': 0,
            'taux_occupation': 0,
            'etudiants_touches': 0,
            'graph_labels': [],
            'graph_data': [],
            'liste_cours': []
        }

    return render_template('dashboard/statistics_professeur.html', stats=stats)


@dashboard_bp.route('/approvals', methods=['GET', 'POST'])
@login_required
def approvals():
    """Page d'approbation des nouveaux administrateurs"""
    from models import Utilisateur
    if current_user.email != 'admin@hestim.ma':
        flash('Accès refusé. Seul le super-administrateur peut accéder à cette page.', 'error')
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        user = Utilisateur.query.get(user_id)
        
        if user and user.role == 'administrateur' and user.email != 'admin@hestim.ma':
            if action == 'approuver':
                user.actif = True
                db.session.commit()
                flash(f"L'administrateur {user.nom} {user.prenom} a été approuvé.", 'success')
            elif action == 'rejeter':
                db.session.delete(user)
                db.session.commit()
                flash(f"La demande de {user.nom} {user.prenom} a été rejetée.", 'info')
                
    # Récupérer les admins en attente
    admins_en_attente = Utilisateur.query.filter_by(role='administrateur', actif=False).all()
    
    return render_template('dashboard/approvals.html', admins_en_attente=admins_en_attente)

