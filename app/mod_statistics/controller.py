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
# Import flask dependencies
import traceback
import json
import os
from flask import Blueprint, render_template, request, url_for, redirect, Response

from app import app
from app.database import db_session
from app.mod_statistics.models import SparkCommandRequest

mod_statistics = Blueprint('mod_statistics', __name__, url_prefix='/stats')


@mod_statistics.route('/')
def show():
    try:
        commands = db_session.query(SparkCommandRequest).all()
        return render_template("stats/spark_stats.html", object=commands)

    except:
        traceback.print_exc()
        return "No response"