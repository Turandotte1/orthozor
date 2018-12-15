#! encoding: utf-8
#! python3

from . import recompense
from flask import render_template
from flask_mab import choose_arm


@recompense.route('/recompense', methods=['GET'])
@choose_arm("image_score_duree")
def recompense(image_score_duree):
    return render_template('recompense/recompense.html', duree=image_score_duree)
