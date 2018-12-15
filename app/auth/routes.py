#! encoding: utf-8
#! python3

from flask import render_template, current_app, redirect, request, url_for, flash

from flask_login import login_user, logout_user, login_required, current_user
from ..models import Utilisateur
from . import auth
from .forms import LoginForm

# Attention, risque d'attaque par injection sur next, à corrriger


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('orthozor.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Utilisateur.query.filter_by(email=form.email.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Adresse email ou mot de passe invalide.')
            return redirect(url_for('.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('orthozor.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Connexion', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.')
    return redirect(url_for('orthozor.index'))
