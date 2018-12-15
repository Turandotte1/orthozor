#! encodeing: utf-8
#! python3


from flask import render_template
from flask_login import login_required, current_user
from . import orthozor
from ..models import Utilisateur


@orthozor.route('/')
@login_required
def index():
    return render_template('orthozor/index.html', user=current_user)


@orthozor.route('/user/<username>/')
def user(username):
    user = Utilisateur.query.filter_by(username=username).first_or_404()
    return render_template('orthozor/user.html', user=user)
