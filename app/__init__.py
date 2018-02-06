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
import os
import json
import traceback

from flask import Flask, render_template, Response, request, redirect, url_for
from sqlalchemy.exc import ProgrammingError

from app.database import db_session
from externalapis.CMXAPICaller import CMXAPICaller
from ciscosparkapi import CiscoSparkAPI
from externalapis.TropoAPICaller import TropoAPICaller
from externalapis.meraki import MerakiHQDemoExtractor

app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))   # refers to application_top

# Configurations
app.config.from_object(os.environ['APP_SETTINGS'])


def get_location_api_extractor():
    output = None
    cmx_controller = get_cmx_controller()
    if cmx_controller:
        output = get_api_cmx(cmx_controller)
    else:
        meraki_controller = get_meraki_controller()
        if meraki_controller:
            output = get_api_meraki(meraki_controller)
    
    return output


def get_api_cmx(cmx_server=None):
    if not cmx_server:
        cmx_server = get_cmx_controller()

    return CMXAPICaller(cmx_server.name, cmx_server.url, cmx_server.username, cmx_server.password)


def get_api_meraki(meraki_server=None):
    if not meraki_server:
        meraki_server = get_meraki_controller()
    if meraki_server.demo_server:
        if meraki_server.name == "Meraki HQ" and "live-map.meraki.com" in meraki_server.demo_server_url:
            return MerakiHQDemoExtractor()
    raise Exception("Feature not ready")


def get_api_spark():
    return CiscoSparkAPI(access_token=app.config['SPARK_TOKEN'])


def get_api_tropo():
    return TropoAPICaller(app.config['TROPO_API_KEY_VOICE'], app.config['TROPO_API_KEY_TEXT'])


def get_notification_sms_phone_number():
    return app.config['NOTIFICATION_SMS_PHONE_NUMBER']


def get_show_web_link():
    return app.config['SHOW_WEB_LINK']


def get_sms_enabled():
    return app.config['SMS_ENABLED']


def get_admin_name():
    return app.config['ADMIN_NAME']


def get_default_room_id():
    return app.config['SPARK_DEFAULT_ROOM_ID']


def get_meraki_validator_token():
    return app.config['MERAKI_VALIDATOR_TOKEN']


def get_secret_key():
    return app.config['SECRET_KEY']


def get_cmx_controller():
    from app.models import CMXServer
    db_controller = db_session.query(CMXServer).filter(CMXServer.active).first()
    return db_controller


def get_meraki_controller():
    from app.models import MerakiServer
    db_controller = db_session.query(MerakiServer).filter(MerakiServer.active).first()
    return db_controller


def get_controller_status():
    if get_cmx_controller() is not None:
        server = 'On-premises'
    elif get_meraki_controller() is not None:
        server = 'Cloud'
    else:
        server = 'None'
    return server


from app.models import CMXServer
from app.mod_cmx_server.controller import mod_cmx_server as cmx_server_mod
from app.mod_meraki_server.controller import mod_meraki_server as meraki_server_mod
from app.mod_cmx_notification.controller import mod_cmx_notification as cmx_notification_mod
from app.mod_api.controller import mod_api as api_mod
from app.mod_monitor.controller import mod_monitor as monitor_mod
from app.mod_user.controller import mod_user as user_mod
from app.mod_simulation.controller import mod_simulation as simulation_mod
from app.mod_engagement.controller import mod_engagement as engagement_mod
from app.mod_error.controller import mod_error as error_mod
from app.mod_spark.controller import mod_spark as spark_mod
from app.mod_server.controller import mod_server as server_mod
from app.mod_statistics.controller import mod_statistics as stats_mod

from app.mod_api import controller as api_controller

# Register blueprint(s)
app.register_blueprint(cmx_server_mod)
app.register_blueprint(meraki_server_mod)
app.register_blueprint(api_mod)
app.register_blueprint(cmx_notification_mod)
app.register_blueprint(monitor_mod)
app.register_blueprint(user_mod)
app.register_blueprint(simulation_mod)
app.register_blueprint(engagement_mod)
app.register_blueprint(error_mod)
app.register_blueprint(spark_mod)
app.register_blueprint(server_mod)
app.register_blueprint(stats_mod)

# app.register_blueprint(xyz_module)
# ..


@app.route('/')
def index():
    return render_template('home/index.html')


@app.route('/clear_db')
@app.route('/clear')
def clear():
    return Response(json.dumps(invoke_db_clear()), mimetype='application/json')


@app.route('/migrate')
def migrate():
    return Response(json.dumps(invoke_db_migration()), mimetype='application/json')


@app.before_first_request
def before_first_request():
    print ("FIRST REQUEST RECEIVED")
    try:
        db_session.query(CMXServer).first()
    except ProgrammingError as e:
        if str(e).__contains__("does not exist"):
            # DB Tables have not been created
            invoke_db_migration()
        else:
            # Unknown error
            raise Exception(e)
    except Exception as e:
        traceback.print_exc()


@app.before_request
def before_request():
    bp = request.blueprint
    # Exempting requests on the root '/something'. i.e. bp = None
    if bp and bp not in [user_mod.name, api_mod.name, error_mod.name, server_mod.name] and bp not in [cmx_notification_mod.name, cmx_server_mod.name] and bp not in [meraki_server_mod.name]:
        if get_cmx_controller() is None and get_meraki_controller() is None:
            return redirect(url_for('mod_error.home', message='You need to set up a server'))


def invoke_db_migration():
    from app.database import init_db
    return init_db()


def invoke_db_clear():
    from app.database import clear_db
    return clear_db()


def invoke_db_close():
    from app.database import close_db
    return close_db()


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return redirect(url_for('mod_error.home', message=404))


@app.teardown_appcontext
def shutdown_session(exception=None):
    if api_controller.too_many_notifications_rows():
        api_controller.update_tables()

    invoke_db_close()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
    #app.run()
