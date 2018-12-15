#! encoding: utf-8
#! python3


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email


class LoginForm(FlaskForm):
    email = StringField('Adresse email', validators=[
                        Required(), Length(1, 64), Email()])
    password = PasswordField('Mot de passe', validators=[Required()])
    remember_me = BooleanField('Rester connecté')
    submit = SubmitField('Connexion')
