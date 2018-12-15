# encoding:utf-8


from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import PasswordField


# Flask-admin
class OrthozorModelView(ModelView):
    page_size = 300
    can_export = True
    #create_modal = True
    edit_modal = True

    # To make columns searchable, or to use them for filtering, specify a list of column names:
    # column_searchable_list = ['name', 'email']
    # column_filters = ['country']
    # For a faster editing experience, enable inline editing in the list view:
    # column_editable_list = ['name', 'last_name']

    def is_accessible(self):
        return current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('auth.login', next=request.url))


class UserView(OrthozorModelView):
    column_exclude_list = ['password_hash', 'avatar_hash']
    form_excluded_columns = ('password_hash', 'avatar_hash',
                             'niveaux_diff', 'premiere_inscription', 'nb_sessions')
    form_extra_fields = {'password': PasswordField('Password')}
