import threading
import time
from app import app
from database import db
from models import Utilisateur

def run_test():
    client = app.test_client()
    with app.app_context():
        admin = Utilisateur.query.filter_by(role='administrateur').first()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id_utilisateur) if admin else '1'
        sess['_fresh'] = True
    html = client.get('/statistics').data.decode('utf-8')
    with open('test_output.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML saved to test_output.html")

run_test()
