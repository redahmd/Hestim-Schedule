from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
from database import db

class Utilisateur(UserMixin, db.Model):
    """Modèle pour les utilisateurs du système"""
    __tablename__ = 'utilisateur'
    
    id_utilisateur = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('administrateur', 'enseignant', 'etudiant', name='role_enum'), nullable=False, index=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)
    
    # Relations
    reservations = db.relationship('Reservation', backref='utilisateur', lazy=True)
    notifications = db.relationship('Notification', backref='utilisateur', lazy=True)
    
    def get_id(self):
        return self.id_utilisateur
    
    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)
    
    def __repr__(self):
        return f'<Utilisateur {self.email}>'

class Professeur(db.Model):
    """Modèle pour les professeurs"""
    __tablename__ = 'professeur'
    
    id_professeur = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    specialite = db.Column(db.String(200), index=True)
    telephone = db.Column(db.String(20))
    departement = db.Column(db.String(100))
    actif = db.Column(db.Boolean, default=True)
    
    # Relations
    cours = db.relationship('Cours', backref='professeur', lazy=True)
    disponibilites = db.relationship('DisponibiliteProfesseur', backref='professeur', lazy=True)
    
    def __repr__(self):
        return f'<Professeur {self.prenom} {self.nom}>'

class Groupe(db.Model):
    """Modèle pour les groupes d'étudiants"""
    __tablename__ = 'groupe'
    
    id_groupe = db.Column(db.Integer, primary_key=True)
    nom_groupe = db.Column(db.String(50), unique=True, nullable=False)
    niveau = db.Column(db.String(50), nullable=False, index=True)
    filiere = db.Column(db.String(100), index=True)
    effectif = db.Column(db.Integer, nullable=False)
    annee_academique = db.Column(db.String(20))
    
    # Relations
    etudiants = db.relationship('Etudiant', backref='groupe', lazy=True)
    cours = db.relationship('Cours', backref='groupe', lazy=True)
    
    def __repr__(self):
        return f'<Groupe {self.nom_groupe}>'

class Etudiant(db.Model):
    """Modèle pour les étudiants"""
    __tablename__ = 'etudiant'
    
    id_etudiant = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    niveau = db.Column(db.String(50))
    id_groupe = db.Column(db.Integer, db.ForeignKey('groupe.id_groupe'), nullable=True)
    date_inscription = db.Column(db.Date)
    actif = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Etudiant {self.prenom} {self.nom}>'

class Salle(db.Model):
    """Modèle pour les salles"""
    __tablename__ = 'salle'
    
    id_salle = db.Column(db.Integer, primary_key=True)
    numero_salle = db.Column(db.String(20), unique=True, nullable=False)
    batiment = db.Column(db.String(50))
    type_salle = db.Column(db.Enum('amphi', 'classe', 'labo_informatique', 'labo_sciences', 'salle_reunion', name='type_salle_enum'), nullable=False, index=True)
    capacite = db.Column(db.Integer, nullable=False, index=True)
    equipement_video = db.Column(db.Boolean, default=False)
    equipement_informatique = db.Column(db.Boolean, default=False)
    tableau_interactif = db.Column(db.Boolean, default=False)
    climatisation = db.Column(db.Boolean, default=False)
    statut = db.Column(db.Enum('disponible', 'en_maintenance', 'hors_service', name='statut_salle_enum'), default='disponible', index=True)
    
    # Relations
    reservations = db.relationship('Reservation', backref='salle', lazy=True)
    
    def __repr__(self):
        return f'<Salle {self.numero_salle}>'
    
    def est_disponible(self, creneau_id):
        """Vérifie si la salle est disponible pour un créneau donné"""
        conflit = Reservation.query.filter_by(
            id_salle=self.id_salle,
            id_creneau=creneau_id,
            statut='confirmee'
        ).first()
        return conflit is None

class Cours(db.Model):
    """Modèle pour les cours"""
    __tablename__ = 'cours'
    
    id_cours = db.Column(db.Integer, primary_key=True)
    nom_cours = db.Column(db.String(200), nullable=False)
    code_cours = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre_heures = db.Column(db.Integer, nullable=False)
    type_cours = db.Column(db.Enum('CM', 'TD', 'TP', 'projet', 'examen', name='type_cours_enum'), nullable=False, index=True)
    id_professeur = db.Column(db.Integer, db.ForeignKey('professeur.id_professeur'), nullable=False, index=True)
    id_groupe = db.Column(db.Integer, db.ForeignKey('groupe.id_groupe'), nullable=False, index=True)
    semestre = db.Column(db.Integer)
    coefficient = db.Column(db.Numeric(3, 1))
    
    # Relations
    reservations = db.relationship('Reservation', backref='cours', lazy=True)
    
    def __repr__(self):
        return f'<Cours {self.code_cours}: {self.nom_cours}>'

class Creneau(db.Model):
    """Modèle pour les créneaux horaires"""
    __tablename__ = 'creneau'
    
    id_creneau = db.Column(db.Integer, primary_key=True)
    jour = db.Column(db.Date, nullable=False, index=True)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    periode = db.Column(db.Enum('matin', 'apres-midi', 'soir', name='periode_enum'), nullable=False, index=True)
    
    # Relations
    reservations = db.relationship('Reservation', backref='creneau', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('jour', 'heure_debut', 'heure_fin', name='unique_creneau'),)
    
    def __repr__(self):
        return f'<Creneau {self.jour} {self.heure_debut}-{self.heure_fin}>'
    
    def chevauche(self, autre_creneau):
        """Vérifie si ce créneau chevauche avec un autre"""
        if self.jour != autre_creneau.jour:
            return False
        return not (self.heure_fin <= autre_creneau.heure_debut or 
                   self.heure_debut >= autre_creneau.heure_fin)

class Reservation(db.Model):
    """Modèle pour les réservations (table centrale)"""
    __tablename__ = 'reservation'
    
    id_reservation = db.Column(db.Integer, primary_key=True)
    id_cours = db.Column(db.Integer, db.ForeignKey('cours.id_cours'), nullable=False, index=True)
    id_salle = db.Column(db.Integer, db.ForeignKey('salle.id_salle'), nullable=False, index=True)
    id_creneau = db.Column(db.Integer, db.ForeignKey('creneau.id_creneau'), nullable=False, index=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id_utilisateur'), nullable=False)
    date_reservation = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.Enum('confirmee', 'en_attente', 'annulee', name='statut_reservation_enum'), default='confirmee', index=True)
    commentaire = db.Column(db.Text)
    modifie_le = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('id_salle', 'id_creneau', 'statut', name='unique_reservation_salle_creneau'),
    )
    
    def __repr__(self):
        return f'<Reservation {self.id_reservation}>'
    
    def verifier_conflits(self):
        """Vérifie les conflits potentiels pour cette réservation"""
        conflits = []
        
        # Conflit de salle (même salle, même créneau)
        conflit_salle = Reservation.query.filter(
            Reservation.id_salle == self.id_salle,
            Reservation.id_creneau == self.id_creneau,
            Reservation.statut == 'confirmee',
            Reservation.id_reservation != self.id_reservation
        ).first()
        
        if conflit_salle:
            conflits.append({
                'type': 'salle',
                'message': f'La salle est déjà réservée pour ce créneau'
            })
        
        # Conflit de professeur (même professeur, même créneau)
        cours = Cours.query.get(self.id_cours)
        if cours:
            autres_reservations = Reservation.query.join(Cours).filter(
                Cours.id_professeur == cours.id_professeur,
                Reservation.id_creneau == self.id_creneau,
                Reservation.statut == 'confirmee',
                Reservation.id_reservation != self.id_reservation
            ).all()
            
            if autres_reservations:
                conflits.append({
                    'type': 'professeur',
                    'message': f'Le professeur a déjà un cours à ce créneau'
                })
        
        # Conflit de groupe (même groupe, même créneau)
        if cours:
            autres_reservations_groupe = Reservation.query.join(Cours).filter(
                Cours.id_groupe == cours.id_groupe,
                Reservation.id_creneau == self.id_creneau,
                Reservation.statut == 'confirmee',
                Reservation.id_reservation != self.id_reservation
            ).all()
            
            if autres_reservations_groupe:
                conflits.append({
                    'type': 'groupe',
                    'message': f'Le groupe a déjà un cours à ce créneau'
                })
        
        return conflits

class DisponibiliteProfesseur(db.Model):
    """Modèle pour les disponibilités des professeurs"""
    __tablename__ = 'disponibilite_professeur'
    
    id_disponibilite = db.Column(db.Integer, primary_key=True)
    id_professeur = db.Column(db.Integer, db.ForeignKey('professeur.id_professeur'), nullable=False, index=True)
    jour_semaine = db.Column(db.Enum('lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', name='jour_semaine_enum'), nullable=False, index=True)
    heure_debut = db.Column(db.Time, nullable=False)
    heure_fin = db.Column(db.Time, nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    recurrent = db.Column(db.Boolean, default=True)
    date_debut = db.Column(db.Date)
    date_fin = db.Column(db.Date)
    
    def __repr__(self):
        return f'<DisponibiliteProfesseur {self.jour_semaine}>'

class Notification(db.Model):
    """Modèle pour les notifications"""
    __tablename__ = 'notification'
    
    id_notification = db.Column(db.Integer, primary_key=True)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey('utilisateur.id_utilisateur'), nullable=False, index=True)
    type_notification = db.Column(db.Enum('reservation', 'modification', 'annulation', 'rappel', 'conflit', name='type_notification_enum'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_envoi = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    lu = db.Column(db.Boolean, default=False, index=True)
    id_reservation = db.Column(db.Integer, db.ForeignKey('reservation.id_reservation'), nullable=True)
    
    def __repr__(self):
        return f'<Notification {self.type_notification}>'

class AuditLog(db.Model):
    """Modèle pour l'audit des modifications"""
    __tablename__ = 'audit_log'
    
    id_log = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False, index=True)
    action = db.Column(db.Enum('INSERT', 'UPDATE', 'DELETE', name='action_enum'), nullable=False)
    id_enregistrement = db.Column(db.Integer)
    id_utilisateur = db.Column(db.Integer)
    date_action = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    donnees_avant = db.Column(db.JSON)
    donnees_apres = db.Column(db.JSON)
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.table_name}>'


