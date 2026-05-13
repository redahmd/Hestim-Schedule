import os
from dotenv import load_dotenv
from routes.reservations import envoyer_email_notification

def envoyer_les_4_tests():
    print("="*60)
    print("📧 CONFIGURATION DU TEST D'ENVOI D'EMAILS")
    print("="*60)
    
    # Load configuration from .env
    load_dotenv()
    
    sender_email = os.environ.get("MAIL_USERNAME")
    sender_password = os.environ.get("MAIL_PASSWORD")
    
    if not sender_email or not sender_password or sender_email == 'hestimschedule@gmail.com' and sender_password == 'votre_mot_de_passe_application_ici':
        print("❌ ERREUR: Le fichier .env n'est pas correctement configuré.")
        print("Veuillez ouvrir le fichier .env et renseigner le MAIL_PASSWORD (mot de passe d'application).")
        return
        
    destinataire = "redahmd721@gmail.com"
    
    # 1. Confirmation de réservation
    sujet1 = "✅ Confirmation de Réservation - Hestim Schedule"
    corps1 = """Bonjour Reda,
    
Votre réservation pour le cours de **Data Science** a été confirmée avec succès.
Date : Lundi 15 Mai 2026
Heure : 09:00 - 10:45
Salle : Labo Informatique 2

Cordialement,
L'équipe Hestim Schedule"""

    # 2. Modification
    sujet2 = "🔄 Modification de votre séance - Hestim Schedule"
    corps2 = """Bonjour Reda,
    
Suite à un changement d'emploi du temps, votre séance de **Développement Web** a été reportée.
Nouvelle Date : Mardi 16 Mai 2026
Nouvelle Heure : 13:30 - 15:15
Salle : Salle 104 (Bâtiment A)

Merci d'en prendre note.
L'équipe Hestim Schedule"""

    # 3. Annulation
    sujet3 = "❌ Annulation de cours - Hestim Schedule"
    corps3 = """Bonjour Reda,
    
Nous vous informons que la séance de **Bases de données avancées** prévue le Jeudi 18 Mai 2026 a été **annulée** en raison d'une absence exceptionnelle de l'enseignant.
Une séance de rattrapage sera programmée ultérieurement.

Cordialement,
L'équipe Hestim Schedule"""

    # 4. Rappel
    sujet4 = "⏰ Rappel de séance imminente - Hestim Schedule"
    corps4 = """Bonjour Reda,
    
Ceci est un rappel pour votre cours qui commence dans moins de 24h :
Cours : **Architecture Logicielle**
Demain à 09:00 en salle Amphi B.

N'oubliez pas d'apporter votre matériel de TP.

Cordialement,
L'équipe Hestim Schedule"""

    emails = [
        (sujet1, corps1),
        (sujet2, corps2),
        (sujet3, corps3),
        (sujet4, corps4)
    ]
    
    print("\n🚀 Démarrage de l'envoi des 4 emails de test...")
    for i, (sujet, corps) in enumerate(emails, 1):
        print(f"Envoi du mail {i}/4 : {sujet}...")
        succes = envoyer_email_notification(destinataire, sujet, corps)
        if succes:
            print("-> ✅ Réussi")
        else:
            print("-> ❌ Échec")
            
    print("\n🎉 Terminé ! Vérifiez la boîte de réception de", destinataire)

if __name__ == "__main__":
    envoyer_les_4_tests()
