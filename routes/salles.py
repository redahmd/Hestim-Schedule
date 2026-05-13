from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from database import db
from models import Salle, Creneau, Reservation
from datetime import date, datetime

salles_bp = Blueprint('salles', __name__)

@salles_bp.route('/')
@login_required
def liste():
    """Liste des salles disponibles"""
    type_salle = request.args.get('type', '')
    statut = request.args.get('statut', 'disponible')
    recherche = request.args.get('recherche', '')
    
    query = Salle.query
    
    if type_salle:
        query = query.filter_by(type_salle=type_salle)
    
    if statut:
        query = query.filter_by(statut=statut)
    
    if recherche:
        query = query.filter(
            db.or_(
                Salle.numero_salle.contains(recherche),
                Salle.batiment.contains(recherche)
            )
        )
    
    query = query.order_by(Salle.numero_salle)
    salles = query.all()
    
    # Determiner les salles occupées actuellement
    from datetime import datetime
    now = datetime.now()
    current_time = now.time()
    today = now.date()
    
    occupied_query = db.session.query(Reservation.id_salle).join(Creneau).filter(
        Reservation.statut == 'confirmee',
        Creneau.jour == today,
        Creneau.heure_debut <= current_time,
        Creneau.heure_fin > current_time
    )
    
    occupied_salle_ids = {r[0] for r in occupied_query.all()}
    
    return render_template('salles/liste.html', salles=salles, 
                         type_salle=type_salle, statut=statut, recherche=recherche,
                         occupied_salle_ids=occupied_salle_ids)

@salles_bp.route('/<int:id>')
@login_required
def detail(id):
    """Détails d'une salle"""
    salle = Salle.query.get_or_404(id)
    
    # Réservations à venir
    reservations = Reservation.query.join(Creneau).filter(
        Reservation.id_salle == id,
        Reservation.statut == 'confirmee',
        Creneau.jour >= date.today()
    ).order_by(Creneau.jour, Creneau.heure_debut).all()
    
    return render_template('salles/detail.html', salle=salle, reservations=reservations)

@salles_bp.route('/disponibles', methods=['POST'])
@login_required
def disponibles():
    """API pour obtenir les salles disponibles pour un créneau"""
    data = request.get_json()
    jour = data.get('jour')
    heure_debut = data.get('heure_debut')
    heure_fin = data.get('heure_fin')
    type_salle = data.get('type_salle')
    capacite_min = data.get('capacite_min')
    
    if not all([jour, heure_debut, heure_fin]):
        return jsonify({'error': 'Paramètres manquants'}), 400
    
    # Créer ou trouver le créneau
    from datetime import datetime, time as time_obj
    jour_date = datetime.strptime(jour, '%Y-%m-%d').date()
    heure_debut_time = datetime.strptime(heure_debut, '%H:%M').time()
    heure_fin_time = datetime.strptime(heure_fin, '%H:%M').time()
    
    # Déterminer la période
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
        db.session.commit()
    
    # Salles disponibles
    query = Salle.query.filter_by(statut='disponible')
    
    if type_salle:
        query = query.filter_by(type_salle=type_salle)
    
    if capacite_min:
        query = query.filter(Salle.capacite >= capacite_min)
    
    salles = query.all()
    salles_disponibles = []
    
    for salle in salles:
        # Vérifier si la salle est réservée pour ce créneau
        reservation = Reservation.query.filter_by(
            id_salle=salle.id_salle,
            id_creneau=creneau.id_creneau,
            statut='confirmee'
        ).first()
        
        if not reservation:
            salles_disponibles.append({
                'id': salle.id_salle,
                'numero': salle.numero_salle,
                'batiment': salle.batiment,
                'type': salle.type_salle,
                'capacite': salle.capacite,
                'equipements': {
                    'video': salle.equipement_video,
                    'informatique': salle.equipement_informatique,
                    'tableau_interactif': salle.tableau_interactif,
                    'climatisation': salle.climatisation
                }
            })
    
    return jsonify({'salles': salles_disponibles})


@salles_bp.route('/creer', methods=['GET', 'POST'])
@login_required
def creer():
    """Créer une nouvelle salle (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé. Seuls les administrateurs peuvent ajouter des salles.', 'error')
        return redirect(url_for('salles.liste'))
    
    if request.method == 'POST':
        try:
            numero_salle = request.form.get('numero_salle')
            batiment = request.form.get('batiment')
            type_salle = request.form.get('type_salle')
            capacite = request.form.get('capacite')
            statut = request.form.get('statut')
            
            # Équipements (checkboxes)
            equipement_video = request.form.get('equipement_video') == 'on'
            equipement_informatique = request.form.get('equipement_informatique') == 'on'
            tableau_interactif = request.form.get('tableau_interactif') == 'on'
            climatisation = request.form.get('climatisation') == 'on'
            
            # Validation
            if not numero_salle or not type_salle or not capacite:
                flash('Veuillez remplir tous les champs obligatoires.', 'error')
                return render_template('salles/creer.html')
            
            if Salle.query.filter_by(numero_salle=numero_salle).first():
                flash('Une salle avec ce numéro existe déjà.', 'error')
                return render_template('salles/creer.html')
            
            try:
                capacite = int(capacite)
                if capacite <= 0:
                     raise ValueError
            except ValueError:
                 flash('La capacité doit être un nombre positif.', 'error')
                 return render_template('salles/creer.html')
                 
            nouvelle_salle = Salle(
                numero_salle=numero_salle,
                batiment=batiment,
                type_salle=type_salle,
                capacite=capacite,
                statut=statut,
                equipement_video=equipement_video,
                equipement_informatique=equipement_informatique,
                tableau_interactif=tableau_interactif,
                climatisation=climatisation
            )
            
            db.session.add(nouvelle_salle)
            db.session.commit()
            
            flash('Salle créée avec succès !', 'success')
            return redirect(url_for('salles.liste'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la salle: {str(e)}', 'error')
    
    # GET: Afficher le formulaire
    return render_template('salles/creer.html')

@salles_bp.route('/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier(id):
    """Modifier une salle existante (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé. Seuls les administrateurs peuvent modifier des salles.', 'error')
        return redirect(url_for('salles.liste'))
    
    salle = Salle.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # On ne modifie pas le numéro si c'est le même (pour éviter l'erreur d'unicité)
            nouveau_numero = request.form.get('numero_salle')
            if nouveau_numero != salle.numero_salle and Salle.query.filter_by(numero_salle=nouveau_numero).first():
                flash('Une salle avec ce numéro existe déjà.', 'error')
                return render_template('salles/modifier.html', salle=salle)
            
            salle.numero_salle = nouveau_numero
            salle.batiment = request.form.get('batiment')
            salle.type_salle = request.form.get('type_salle')
            salle.statut = request.form.get('statut')
            
            try:
                capacite = int(request.form.get('capacite'))
                if capacite <= 0:
                     raise ValueError
                salle.capacite = capacite
            except ValueError:
                 flash('La capacité doit être un nombre positif.', 'error')
                 return render_template('salles/modifier.html', salle=salle)
            
            salle.equipement_video = request.form.get('equipement_video') == 'on'
            salle.equipement_informatique = request.form.get('equipement_informatique') == 'on'
            salle.tableau_interactif = request.form.get('tableau_interactif') == 'on'
            salle.climatisation = request.form.get('climatisation') == 'on'
            
            db.session.commit()
            
            flash('Salle modifiée avec succès !', 'success')
            return redirect(url_for('salles.liste'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification de la salle: {str(e)}', 'error')
            
    return render_template('salles/modifier.html', salle=salle)

@salles_bp.route('/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer(id):
    """Supprimer une salle (administrateur uniquement)"""
    if current_user.role != 'administrateur':
        flash('Accès refusé.', 'error')
        return redirect(url_for('salles.liste'))
    
    salle = Salle.query.get_or_404(id)
    
    try:
        # Vérifier s'il y a des réservations futures
        reservations = Reservation.query.filter_by(id_salle=id).count()
        if reservations > 0:
             flash(f'Impossible de supprimer cette salle car elle a {reservations} réservation(s) associée(s).', 'error')
             return redirect(url_for('salles.liste'))
        
        db.session.delete(salle)
        db.session.commit()
        flash('Salle supprimée avec succès.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
        
    return redirect(url_for('salles.liste'))

