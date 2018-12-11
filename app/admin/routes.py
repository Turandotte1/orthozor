#! encoding: utf-8
#! python3

from flask import render_template#, current_app, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required
#from ..models import Utilisateur
from . import admin
#from .forms import LoginForm

@admin.route('/accueil', methods=['GET', 'POST'])
def accueil_admin():
    return render_template('admin/accueil.html')


@admin.route('/test', methods=['GET', 'POST'])
def test_admin():
    return render_template('admin/footer_admin.html')    
    
# @auth.route('/logout')
# @login_required
# def logout():
    # logout_user()
    # flash('Vous avez été déconnecté.')
    # return redirect(url_for('orthozor.index'))
