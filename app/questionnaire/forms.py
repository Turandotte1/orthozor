#! encoding: utf-8
#! python3

from flask_wtf import FlaskForm as Form
#from wtforms.validators import Required
from wtforms.fields import TextField, SubmitField



class QuestionForm(Form):
    answer = TextField('Réponse', validators=[])
    submit = SubmitField('Valider')