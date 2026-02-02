from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, ValidationError, Optional
import re

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(message="Le nom d'utilisateur est requis"),
        Length(min=3, max=80)
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(message="Le mot de passe est requis")
    ])
    submit = SubmitField('Se connecter')

class EmployeeForm(FlaskForm):
    nom = StringField('Nom', validators=[
        DataRequired(message="Le nom est requis"),
        Length(min=2, max=100, message="Le nom doit contenir entre 2 et 100 caractères")
    ])
    prenom = StringField('Prénom', validators=[
        DataRequired(message="Le prénom est requis"),
        Length(min=2, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(message="L'email est requis"),
        Email(message="Email invalide")
    ])
    telephone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    departement = SelectField('Département', choices=[
        ('', 'Sélectionner...'),
        ('IT', 'IT'),
        ('RH', 'Ressources Humaines'),
        ('Finance', 'Finance'),
        ('Marketing', 'Marketing'),
        ('Commercial', 'Commercial'),
        ('Direction', 'Direction')
    ])
    poste = StringField('Poste', validators=[
        DataRequired(message="Le poste est requis"),
        Length(min=2, max=100)
    ])
    salaire = FloatField('Salaire (€)', validators=[
        DataRequired(message="Le salaire est requis"),
        NumberRange(min=0, message="Le salaire doit être positif")
    ])
    date_embauche = DateField('Date d\'embauche', validators=[
        DataRequired(message="La date d'embauche est requise")
    ])
    submit = SubmitField('Enregistrer')
    
    def validate_telephone(self, field):
        if field.data:
            # Accepte les formats: 0123456789, 01 23 45 67 89, +33 1 23 45 67 89
            pattern = r'^[\d\s\+\-\.]+$'
            if not re.match(pattern, field.data):
                raise ValidationError("Format de téléphone invalide")

class UserForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Mot de passe', validators=[
        DataRequired(),
        Length(min=8, message="Le mot de passe doit contenir au moins 8 caractères")
    ])
    role = SelectField('Rôle', choices=[
        ('readonly', 'Lecture seule'),
        ('rh', 'RH'),
        ('admin', 'Administrateur')
    ])
    submit = SubmitField('Créer')