from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import pandas as pd
from io import BytesIO, StringIO
import csv
import datetime
import sqlite3

# Création de la base si elle n'existe pas
def init_db():
    conn = sqlite3.connect("huma_rh.db")  # même nom que partout dans ton code
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            prenom TEXT,
            departement TEXT,
            poste TEXT,
            salaire REAL
        )
    """)
    conn.commit()
    conn.close()


# Appelé au démarrage de l'application
init_db()

app = Flask(__name__)
app.secret_key = 'huma-rh-2026-super-secret-key-change-in-production'
app.permanent_session_lifetime = timedelta(hours=2)

# Admin par défaut (login: admin / mdp: admin123)
ADMIN_CREDENTIALS = {
    'admin': generate_password_hash('admin123')
}

def get_db_connection():
    conn = sqlite3.connect('huma_rh.db')
    conn.row_factory = sqlite3.Row
    return conn


def login_required(f):
    def wrap(*args, **kwargs):
        if 'user' not in session:
            flash('🔐 Accès refusé ! Veuillez vous connecter.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in ADMIN_CREDENTIALS and check_password_hash(ADMIN_CREDENTIALS[username], password):
            session['user'] = username
            session.permanent = True
            flash('✅ Connexion réussie !', 'success')
            return redirect(url_for('index'))
        else:
            flash('❌ Identifiants incorrects !', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('👋 Déconnexion réussie', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    conn.close()
    return render_template('index.html', total=total)

@app.route('/employes')
@login_required
def liste_employes():
    conn = get_db_connection()
    recherche = request.args.get('recherche', '')
    departement = request.args.get('departement', '')
    salaire_min = request.args.get('salaire_min', '')
    
    query = 'SELECT * FROM employees WHERE 1=1'
    params = []
    
    if recherche:
        query += ' AND (nom LIKE ? OR prenom LIKE ? OR email LIKE ?)'
        params.extend([f'%{recherche}%', f'%{recherche}%', f'%{recherche}%'])
    
    if departement:
        query += ' AND departement = ?'
        params.append(departement)
    
    if salaire_min:
        query += ' AND salaire >= ?'
        params.append(float(salaire_min))
    
    query += ' ORDER BY nom'
    
    employees = conn.execute(query, params).fetchall()
    
    total_employes = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    salaire_moyen = conn.execute('SELECT AVG(salaire) FROM employees').fetchone()[0] or 0
    
    conn.close()
    return render_template('employes.html', 
                         employees=employees,
                         total_employes=total_employes,
                         salaire_moyen=salaire_moyen,
                         recherche=recherche,
                         departement=departement,
                         salaire_min=salaire_min)

@app.route('/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_employe():
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO employees (nom, prenom, email, telephone, poste, salaire, date_embauche, departement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['nom'],
                request.form['prenom'],
                request.form['email'],
                request.form['telephone'],
                request.form['poste'],
                float(request.form['salaire']),
                request.form['date_embauche'],
                request.form['departement']
            ))
            conn.commit()
            flash('✅ Employé ajouté avec succès !', 'success')
        except sqlite3.IntegrityError:
            flash('❌ Erreur : Email déjà utilisé !', 'error')
        finally:
            conn.close()
        return redirect(url_for('liste_employes'))
    
    return render_template('ajouter.html')

@app.route('/modifier/<int:employe_id>', methods=['GET', 'POST'])
@login_required
def modifier_employe(employe_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        try:
            conn.execute('''
                UPDATE employees SET 
                nom=?, prenom=?, email=?, telephone=?, poste=?, salaire=?, date_embauche=?, departement=?
                WHERE id=?
            ''', (
                request.form['nom'],
                request.form['prenom'],
                request.form['email'],
                request.form['telephone'],
                request.form['poste'],
                float(request.form['salaire']),
                request.form['date_embauche'],
                request.form['departement'],
                employe_id
            ))
            conn.commit()
            flash('✅ Employé modifié avec succès !', 'success')
        except sqlite3.IntegrityError:
            flash('❌ Erreur : Email déjà utilisé !', 'error')
        finally:
            conn.close()
        return redirect(url_for('liste_employes'))
    
    employe = conn.execute('SELECT * FROM employees WHERE id = ?', (employe_id,)).fetchone()
    conn.close()
    
    if employe is None:
        flash('❌ Employé non trouvé !', 'error')
        return redirect(url_for('liste_employes'))
    
    return render_template('modifier.html', employe=employe)

@app.route('/supprimer/<int:employe_id>')
@login_required
def supprimer_employe(employe_id):
    conn = get_db_connection()
    employe = conn.execute('SELECT nom, prenom FROM employees WHERE id = ?', (employe_id,)).fetchone()
    if employe:
        conn.execute('DELETE FROM employees WHERE id = ?', (employe_id,))
        conn.commit()
        flash(f'✅ {employe["prenom"]} {employe["nom"]} supprimé !', 'success')
    else:
        flash('❌ Employé non trouvé !', 'error')
    conn.close()
    return redirect(url_for('liste_employes'))
@app.route('/init_departements')
def init_departements():
    import sqlite3
    def init_db():
    conn = sqlite3.connect("huma_rh.db")  # remplace par ton vrai nom de fichier
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            prenom TEXT,
            departement TEXT,
            poste TEXT,
            salaire REAL,
            date_embauche DATE
        )
    """)
    conn.commit()
    conn.close()

@app.route('/stats')
@login_required
def dashboard_stats():
    conn = get_db_connection()
    
    total_employes = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    salaire_moyen = conn.execute('SELECT AVG(salaire) FROM employees').fetchone()[0] or 0
    salaire_total = conn.execute('SELECT SUM(salaire) FROM employees').fetchone()[0] or 0
    salaire_median = conn.execute('SELECT AVG(salaire) FROM (SELECT salaire FROM employees ORDER BY salaire LIMIT 2 OFFSET ((SELECT COUNT(*) FROM employees) - 1)/2)').fetchone()[0] or 0
    
    depts = conn.execute('''
        SELECT departement, COUNT(*) as count, AVG(salaire) as avg_salaire, SUM(salaire) as total_salaire
        FROM employees WHERE departement IS NOT NULL GROUP BY departement ORDER BY count DESC
    ''').fetchall()
    
    top_salaires = conn.execute('''
        SELECT nom, prenom, poste, salaire, departement 
        FROM employees ORDER BY salaire DESC LIMIT 5
    ''').fetchall()
    
    evolution = conn.execute('''
        SELECT strftime('%Y', date_embauche) as annee, COUNT(*) as embauches, AVG(salaire) as salaire_moyen
        FROM employees GROUP BY annee ORDER BY annee
    ''').fetchall()
    
    conn.close()
    
    return render_template('stats.html', 
                         total_employes=total_employes,
                         salaire_moyen=salaire_moyen,
                         salaire_total=salaire_total,
                         salaire_median=salaire_median,
                         depts=depts,
                         top_salaires=top_salaires,
                         evolution=evolution)

@app.route('/fix_columns')
def fix_columns():
    import sqlite3
    conn = sqlite3.connect("huma_rh.db")  # mets ici le même nom de fichier que dans le reste de ton code
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE employees ADD COLUMN departement TEXT")
        cursor.execute("ALTER TABLE employees ADD COLUMN date_embauche DATE")
        conn.commit()
        msg = "Colonnes ajoutées : departement, date_embauche"
    except Exception as e:
        msg = f"Erreur (colonnes déjà créées ?) : {e}"
    finally:
        conn.close()
    return msg

@app.route('/export/csv')
@login_required
def export_csv():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees ORDER BY nom').fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Prénom', 'Email', 'Téléphone', 'Poste', 'Salaire (€)', 'Date Embauche', 'Département'])
    
    for emp in employees:
        writer.writerow([
            emp['id'], emp['nom'], emp['prenom'], emp['email'], 
            emp['telephone'] or '', emp['poste'], f"{emp['salaire']:.2f}",
            emp['date_embauche'], emp['departement'] or ''
        ])
    
    return app.response_class(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=huma_rh.csv'}
    )

@app.route('/export/excel')
@login_required
def export_excel():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees ORDER BY nom').fetchall()
    conn.close()
    
    df = pd.DataFrame([dict(emp) for emp in employees])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Employés', index=False)
    output.seek(0)
    
    return app.response_class(
        output.read(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment;filename=huma_rh.xlsx'}
    )
# 🔥 COMANDES UTILITAIRES (tape dans PowerShell)
@app.cli.command('init')
def init_command():
    """Initialise la base de données"""
    init_db()
    print("✅ Base de données initialisée !")

@app.cli.command('stats')
def stats_command():
    """Affiche les statistiques rapides"""
    conn = get_db_connection()
    total = conn.execute('SELECT COUNT(*) FROM employees').fetchone()[0]
    moyenne = conn.execute('SELECT AVG(salaire) FROM employees').fetchone()[0] or 0
    total_masse = conn.execute('SELECT SUM(salaire) FROM employees').fetchone()[0] or 0
    conn.close()
    print(f"📊 STATS: {total} employés | Moyenne: {moyenne:.0f}€ | Masse salariale: {total_masse:.0f}€")

@app.cli.command('reset')
def reset_command():
    """⚠️ SUPPRIME TOUS les employés (ATTENTION!)"""
    confirm = input("⚠️ Êtes-vous SÛR? Tape 'OUI' : ")
    if confirm == 'OUI':
        conn = get_db_connection()
        conn.execute('DELETE FROM employees')
        conn.commit()
        conn.close()
        print("🗑️ Base VIDE !")
    else:
        print("❌ Annulé")

@app.cli.command('add-demo')
def add_demo_command():
    """Ajoute 10 employés DE TEST"""
    conn = get_db_connection()
    demos = [
        ('Dupont', 'Jean', 'jean.dupont@entreprise.fr', '0123456789', 'Développeur', 3800, '2025-01-15', 'IT'),
        ('Martin', 'Marie', 'marie.martin@entreprise.fr', '0987654321', 'RH Manager', 4200, '2024-06-01', 'RH'),
        ('Leroy', 'Paul', 'paul.leroy@entreprise.fr', '', 'Data Analyst', 3500, '2025-03-10', 'IT'),
        ('Dubois', 'Sophie', 'sophie.dubois@entreprise.fr', '0112233445', 'Comptable', 3200, '2024-09-20', 'Finance'),
        ('Bernard', 'Luc', 'luc.bernard@entreprise.fr', '', 'Marketing', 3400, '2025-01-01', 'Marketing'),
    ]
    for nom, prenom, email, tel, poste, salaire, date, dept in demos:
        try:
            conn.execute('INSERT INTO employees (nom, prenom, email, telephone, poste, salaire, date_embauche, departement) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', 
                        (nom, prenom, email, tel, poste, salaire, date, dept))
        except:
            pass
    conn.commit()
    conn.close()
    print("✅ 10 employés DE TEST ajoutés !")

@app.cli.command('help')
def help_command():
    """Affiche toutes les commandes"""
    print("""
🚀 COMANDES HUMA-RH :
  flask init      - Initialise la BDD
  flask stats     - Stats rapides
  flask reset     - SUPPRIME TOUT (⚠️)
  flask add-demo  - Ajoute 10 employés TEST
  flask help      - Cette aide
    """)

if __name__ == '__main__':
    init_db()
    print("🔐 HUMA-RH v4 SECURE démarre sur http://127.0.0.1:5000")
    print("👤 Login: admin | Mot de passe: admin123")
    app.run(debug=True, port=5000)
