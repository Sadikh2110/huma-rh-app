from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from app.models import db, Employee, EmployeeHistory
from app.forms import EmployeeForm
from functools import wraps
from io import StringIO, BytesIO
import csv
import json
import pandas as pd

employees_bp = Blueprint('employees', __name__)

def edit_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.can_edit():
            flash('❌ Vous n\'avez pas les droits de modification', 'error')
            return redirect(url_for('employees.liste'))
        return f(*args, **kwargs)
    return decorated_function

def log_action(employee_id, action, changes=None):
    """Enregistre une action dans l'historique"""
    history = EmployeeHistory(
        employee_id=employee_id,
        user_id=current_user.id,
        action=action,
        changes=json.dumps(changes) if changes else None
    )
    db.session.add(history)

@employees_bp.route('/')
@login_required
def index():
    total = Employee.query.count()
    return render_template('index.html', total=total)

@employees_bp.route('/employes')
@login_required
def liste():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    recherche = request.args.get('recherche', '')
    departement = request.args.get('departement', '')
    salaire_min = request.args.get('salaire_min', '', type=str)
    
    query = Employee.query
    
    if recherche:
        search_term = f'%{recherche}%'
        query = query.filter(
            db.or_(
                Employee.nom.ilike(search_term),
                Employee.prenom.ilike(search_term),
                Employee.email.ilike(search_term)
            )
        )
    
    if departement:
        query = query.filter(Employee.departement == departement)
    
    if salaire_min:
        try:
            query = query.filter(Employee.salaire >= float(salaire_min))
        except ValueError:
            pass
    
    query = query.order_by(Employee.nom)
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    employees = pagination.items
    
    # Stats
    total_employes = Employee.query.count()
    salaire_moyen = db.session.query(db.func.avg(Employee.salaire)).scalar() or 0
    
    # Liste des départements pour le filtre
    departements = db.session.query(Employee.departement).distinct().filter(
        Employee.departement.isnot(None)
    ).all()
    departements = [d[0] for d in departements if d[0]]
    
    return render_template('employes.html',
                         employees=employees,
                         pagination=pagination,
                         total_employes=total_employes,
                         salaire_moyen=salaire_moyen,
                         recherche=recherche,
                         departement=departement,
                         salaire_min=salaire_min,
                         departements=departements)

@employees_bp.route('/ajouter', methods=['GET', 'POST'])
@login_required
@edit_required
def ajouter():
    form = EmployeeForm()
    
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà
        if Employee.query.filter_by(email=form.email.data).first():
            flash('❌ Cet email est déjà utilisé', 'error')
            return render_template('ajouter.html', form=form)
        
        employee = Employee(
            nom=form.nom.data,
            prenom=form.prenom.data,
            email=form.email.data,
            telephone=form.telephone.data,
            departement=form.departement.data,
            poste=form.poste.data,
            salaire=form.salaire.data,
            date_embauche=form.date_embauche.data
        )
        
        db.session.add(employee)
        db.session.flush()  # Pour obtenir l'ID
        
        log_action(employee.id, 'create', {
            'nom': employee.nom,
            'prenom': employee.prenom,
            'email': employee.email
        })
        
        db.session.commit()
        flash(f'✅ {employee.prenom} {employee.nom} ajouté avec succès !', 'success')
        return redirect(url_for('employees.liste'))
    
    return render_template('ajouter.html', form=form)

@employees_bp.route('/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
@edit_required
def modifier(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)
    
    if form.validate_on_submit():
        # Vérifier si l'email existe déjà (sauf pour cet employé)
        existing = Employee.query.filter(
            Employee.email == form.email.data,
            Employee.id != id
        ).first()
        
        if existing:
            flash('❌ Cet email est déjà utilisé', 'error')
            return render_template('modifier.html', form=form, employe=employee)
        
        # Enregistrer les changements pour l'historique
        changes = {}
        for field in ['nom', 'prenom', 'email', 'telephone', 'departement', 'poste', 'salaire']:
            old_value = getattr(employee, field)
            new_value = getattr(form, field).data
            if old_value != new_value:
                changes[field] = {'old': old_value, 'new': new_value}
        
        # Mettre à jour
        form.populate_obj(employee)
        
        if changes:
            log_action(employee.id, 'update', changes)
        
        db.session.commit()
        flash(f'✅ {employee.prenom} {employee.nom} modifié avec succès !', 'success')
        return redirect(url_for('employees.liste'))
    
    return render_template('modifier.html', form=form, employe=employee)

@employees_bp.route('/supprimer/<int:id>', methods=['POST'])
@login_required
@edit_required
def supprimer(id):
    employee = Employee.query.get_or_404(id)
    nom_complet = f"{employee.prenom} {employee.nom}"
    
    log_action(employee.id, 'delete', {
        'nom': employee.nom,
        'prenom': employee.prenom,
        'email': employee.email
    })
    
    db.session.delete(employee)
    db.session.commit()
    
    flash(f'✅ {nom_complet} supprimé !', 'success')
    return redirect(url_for('employees.liste'))

@employees_bp.route('/historique/<int:id>')
@login_required
def historique(id):
    employee = Employee.query.get_or_404(id)
    history = EmployeeHistory.query.filter_by(employee_id=id).order_by(
        EmployeeHistory.timestamp.desc()
    ).all()
    return render_template('historique.html', employee=employee, history=history)

@employees_bp.route('/export/csv')
@login_required
def export_csv():
    employees = Employee.query.order_by(Employee.nom).all()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Nom', 'Prénom', 'Email', 'Téléphone', 'Poste', 'Salaire (€)', 'Date Embauche', 'Département'])
    
    for emp in employees:
        writer.writerow([
            emp.id, emp.nom, emp.prenom, emp.email,
            emp.telephone or '', emp.poste, f"{emp.salaire:.2f}",
            emp.date_embauche.strftime('%Y-%m-%d') if emp.date_embauche else '',
            emp.departement or ''
        ])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=huma_rh_export.csv'}
    )

@employees_bp.route('/export/excel')
@login_required
def export_excel():
    employees = Employee.query.order_by(Employee.nom).all()
    
    data = [{
        'ID': emp.id,
        'Nom': emp.nom,
        'Prénom': emp.prenom,
        'Email': emp.email,
        'Téléphone': emp.telephone or '',
        'Poste': emp.poste,
        'Salaire': emp.salaire,
        'Date Embauche': emp.date_embauche,
        'Département': emp.departement or ''
    } for emp in employees]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Employés', index=False)
    
    output.seek(0)
    
    return Response(
        output.read(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment;filename=huma_rh_export.xlsx'}
    )