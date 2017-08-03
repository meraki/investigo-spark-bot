"""
   Copyright 2017 Rafael Carvalho

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from flask import Blueprint, request, render_template, session, redirect

import app
from app.database import db_session
from app.mod_user.models import RegisteredUser
from app.models import Floor

mod_error = Blueprint('mod_error', __name__, url_prefix='/error')


@mod_error.route('/<message>', methods=['GET'])
@mod_error.route('/', methods=['GET'])
def home(message=None):
    return render_template('_base/error.html', message=message)
