from app import app
from flask import render_template
import sys

with app.test_request_context('/'):
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
        'surcharge_moyenne': 0
    }
    
    # We also need current_user for the base template
    from flask_login import current_user
    # Mock current_user if necessary, though base.html might check current_user.is_authenticated
    # We can just try to render
    try:
        html = render_template('dashboard/statistics.html', stats=stats)
        print("Template rendered successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"Error rendering template: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
