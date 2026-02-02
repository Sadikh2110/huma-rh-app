from flask import Blueprint, render_template
from flask_login import login_required
from app.models import db, Employee

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/stats')
@login_required
def dashboard():
    total_employes = Employee.query.count()
    salaire_moyen = db.session.query(db.func.avg(Employee.salaire)).scalar() or 0
    salaire_total = db.session.query(db.func.sum(Employee.salaire)).scalar() or 0
    
    # Stats par département
    depts = db.session.query(
        Employee.departement,
        db.func.count(Employee.id).label('count'),
        db.func.avg(Employee.salaire).label('avg_salaire'),
        db.func.sum(Employee.salaire).label('total_salaire')
    ).filter(Employee.departement.isnot(None)).group_by(
        Employee.departement
    ).order_by(db.desc('count')).all()
    
    # Top salaires
    top_salaires = Employee.query.order_by(Employee.salaire.desc()).limit(5).all()
    
    # Évolution par année
    evolution = db.session.query(
        db.func.strftime('%Y', Employee.date_embauche).label('annee'),
        db.func.count(Employee.id).label('embauches'),
        db.func.avg(Employee.salaire).label('salaire_moyen')
    ).group_by('annee').order_by('annee').all()
    
    return render_template('stats.html',
                         total_employes=total_employes,
                         salaire_moyen=salaire_moyen,
                         salaire_total=salaire_total,
                         depts=depts,
                         top_salaires=top_salaires,
                         evolution=evolution)