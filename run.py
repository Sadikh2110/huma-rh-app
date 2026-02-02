import os
from app import create_app

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

from apscheduler.schedulers.background import BackgroundScheduler
from backup import backup_database

# Après la création de l'app Flask
scheduler = BackgroundScheduler()
scheduler.add_job(backup_database, 'interval', hours=24)
scheduler.start()

if __name__ == '__main__':
    print("🔐 HUMA-RH v5 SECURE démarre sur http://127.0.0.1:5000")
    print("👤 Login: admin | Mot de passe: admin123")
    app.run(debug=True, port=5000)