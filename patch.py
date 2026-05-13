import io

with io.open('routes/reservations.py', 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'db.session.add(notification)' in line and 'except' in lines[i+1]:
        lines.insert(i+1, '''                
                # ENVOI EMAIL
                envoyer_email_notification(
                    destinataire=current_user.email,
                    sujet="Hestim Schedule - Nouvelle Réservation",
                    corps=f"Bonjour,\\n\\nVotre réservation pour {cours.nom_cours} a été confirmée pour le {jour_date.strftime('%d/%m/%Y')} de {heure_debut_time.strftime('%H:%M')} à {heure_fin_time.strftime('%H:%M')} en salle {salle.numero_salle}.\\n\\nCordialement,\\nHestim Schedule"
                )
''')
        break

with io.open('routes/reservations.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
