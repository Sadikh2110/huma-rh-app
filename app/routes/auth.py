from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User
from app.forms import LoginForm, UserForm
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    return redirect(url_for('auth.login'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('❌ Accès réservé aux administrateurs', 'error')
            return redirect(url_for('employees.index'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('employees.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('❌ Ce compte est désactivé', 'error')
                return render_template('login.html', form=form)
            
            login_user(user, remember=True)
            flash(f'✅ Bienvenue {user.username} !', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('employees.index'))
        else:
            flash('❌ Identifiants incorrects', 'error')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('👋 Déconnexion réussie', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@auth_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('❌ Ce nom d\'utilisateur existe déjà', 'error')
            return render_template('add_user.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('✅ Utilisateur créé avec succès', 'success')
        return redirect(url_for('auth.list_users'))
    
    return render_template('add_user.html', form=form)