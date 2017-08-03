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
import json
import traceback
import cgi
from flask import Blueprint, render_template, request, Response, url_for, redirect

from app import get_api_spark, get_api_tropo, get_default_room_id, get_notification_sms_phone_number
from app.database import db_session
from app.mod_user.models import RegisteredUser
from app.models import Floor, EngagementTrigger, Zone
try:
    from html import unescape  # python 3.4+
except ImportError:
    try:
        from html.parser import HTMLParser  # python 3.x (<3.4)
    except ImportError:
        from HTMLParser import HTMLParser  # python 2.x
    unescape = HTMLParser().unescape



mod_engagement = Blueprint('mod_engagement', __name__, url_prefix='/engagement')


@mod_engagement.route('/', methods=['GET'])
def home():
    output = render_template("engagement/engagement_home.html")
    return output


@mod_engagement.route('/screen/select', methods=['GET', 'POST'])
def engagement_screen_select():
    if request.method == 'GET':
        floors = db_session.query(Floor).all()
        output = render_template("engagement/screen/engagement_select.html", floors=floors)
    else:
        output = redirect(url_for('.engagement_screen_show', hierarchy=request.form['hierarchy']))
    return output


@mod_engagement.route('/screen/<hierarchy>', methods=['GET'])
def engagement_screen_show(hierarchy):
    zone_name = hierarchy.split('>')[-1]
    zone = db_session.query(Zone).filter(Zone.name == zone_name).first()
    triggers = []
    for t in get_engagement_triggers_per_zone(zone.id):
        triggers.append(t.serialize())

    vertical_hierarchy = None
    if zone.vertical_name:
        vertical_hierarchy = zone.get_vertical_hierarchy()

    output = render_template("engagement/screen/engagement_show.html", hierarchy=hierarchy, triggers=triggers, vertical_hierarchy=vertical_hierarchy)
    return output

@mod_engagement.route('/screen_dwell/select', methods=['GET', 'POST'])
def engagement_screen_dwell_select():
    if request.method == 'GET':
        floors = db_session.query(Floor).all()
        output = render_template("engagement/screen/engagement_select.html", floors=floors)
    else:
        output = redirect(url_for('.engagement_screen_dwell_show', hierarchy=request.form['hierarchy']))
    return output

@mod_engagement.route('/screen_dwell/<hierarchy>', methods=['GET'])
def engagement_screen_dwell_show(hierarchy):
    zone_name = hierarchy.split('>')[-1]
    zone = db_session.query(Zone).filter(Zone.name == zone_name).first()

    vertical_hierarchy = None
    if zone.vertical_name:
        vertical_hierarchy = zone.get_vertical_hierarchy()

    output = render_template("engagement/screen/engagement_show_dwell.html", hierarchy=hierarchy, vertical_hierarchy=vertical_hierarchy)
    return output


@mod_engagement.route('/trigger/', methods=['GET'])
def engagement_trigger_list():
    output = render_template("engagement/trigger/trigger_home.html")
    return output


@mod_engagement.route('/trigger/add', methods=['GET'])
def engagement_trigger_add():
    floors = db_session.query(Floor).all()
    users = db_session.query(RegisteredUser).all()
    output = render_template("engagement/trigger/trigger_add.html", users=users, floors=floors, default_room_id=get_default_room_id())
    return output


@mod_engagement.route('/trigger/user/add', methods=['POST'])
def engagement_trigger_user_add():
    output = {
        'error': True,
        'error_message': 'Unknown error',
        'message': None,
    }
    if request.json:
        request_json = request.json
        registered_user_id = request_json['registered_user_id']
        zone_id = request_json['zone']
        event = request_json['event']

        triggers_created = 0
        post_on_spark = 'spark_checkbox' in request_json
        if post_on_spark:
            spark_target = request_json['spark_target']
            spark_value = request_json['spark_value']
            if spark_target and spark_value:
                spark_trigger = EngagementTrigger('spark', spark_target, spark_value, event, zone_id, registered_user_id, extras=None)
                db_session.add(spark_trigger)
                triggers_created += 1

        post_on_tropo = 'tropo_checkbox' in request_json
        if post_on_tropo:
            tropo_target = request_json['tropo_target']
            tropo_platform = request_json['tropo_platform']
            tropo_value = request_json['tropo_value']
            if tropo_target and tropo_platform and tropo_value:
                tropo_trigger = EngagementTrigger('tropo', tropo_target, tropo_value, event, zone_id, registered_user_id, extras=tropo_platform)
                db_session.add(tropo_trigger)
                triggers_created += 1

        try:
            db_session.commit()
            output = {
                'error': False,
                'error_message': None,
                'message': "{} trigger(s) created".format(triggers_created)
            }
        except:
            output = {
                'error': True,
                'error_message': 'Error on trigger creation.',
                'message': None,
            }
            traceback.print_exc()
    else:
        output = {
            'error': True,
            'error_message': 'JSON data not provided on request',
            'message': None,
        }
    return Response(json.dumps(output), mimetype='application/json')


@mod_engagement.route('/trigger/user/<registered_user_id>/view', methods=['GET'])
def engagement_trigger_user_list(registered_user_id):
    # output = render_template("engagement/show.html", hierarchy=hierarchy)
    output = 'Under construction'
    return output


@mod_engagement.route('/trigger/user/fire', methods=['POST'])
def fire_user_zone_trigger():

    try:
        trigger = None
        if request.json:
            trigger = db_session.query(EngagementTrigger).filter(EngagementTrigger.id == request.json['trigger_id']).first()
        if trigger:

            user = db_session.query(RegisteredUser).filter(RegisteredUser.id == trigger.registered_user_id).first()
            zone = db_session.query(Zone).filter(Zone.id == trigger.zone_id).first()
            if user and zone:
                platform = trigger.platform
                text = trigger.value
                text = replace_user_info_on_trigger_text(text, user)
                text = replace_zone_information(text, zone)
                response = None
                if trigger.platform == 'spark':
                    # do action
                    room_id = trigger.target
                    response = get_api_spark().messages.create(roomId=room_id, text=text)
                    ok = response
                elif trigger.platform == 'tropo':
                    number = trigger.target
                    number = replace_user_info_on_trigger_text(number, user)
                    tropo_platform = trigger.extras
                    response = get_api_tropo().triggerTropoWithMessageAndNumber(text, number, voice="dave", type=tropo_platform)
                    ok = response.status_code == 200

                if ok:
                    output = {
                        'error': False,
                        'error_message': None,
                        'message': 'Successfully posted on {}'.format(platform),
                    }
                else:
                    output = {
                        'error': True,
                        'error_message': 'Error when trying to post to on {}'.format(platform),
                        'message': None,
                    }
            else:
                output = {
                    'error': True,
                    'error_message': 'User or Zone not found ids = {} / {}'.format(trigger.registered_user_id, trigger.zone_id),
                    'message': None,
                }
        else:
            output = {
                'error': True,
                'error_message': 'Trigger id not provided as json.',
                'message': None,
            }
    except Exception as e:
        output = {
            'error': True,
            'error_message': 'Unknown error\n{}'.format(str(e)),
            'message': None,
        }
        traceback.print_exc()

    return Response(json.dumps(output), mimetype='application/json')



@mod_engagement.route('/trigger_dwell', methods=['POST'])
def fire_exceeded_dwell_time():
    error = True
    error_message = 'Unknown error'
    message = None
    try:
        if request.json:
            user = db_session.query(RegisteredUser).filter(RegisteredUser.id == request.json['user_id']).first()
            hierarchy = request.json['hierarchy']
            hierarchy_vertical_name = request.json['hierarchy_vertical_name']
            if user:
                h = hierarchy
                if hierarchy_vertical_name:
                    h = hierarchy_vertical_name

                h = unescape(h)

                spark_message = 'Employee {} has stayed for too long at {}'.format(user.name, h)
                get_api_spark().messages.create(get_default_room_id(), text=spark_message)

                if user.phone:
                    tropo_message = 'Please leave {}'.format(h)
                    get_api_tropo().triggerTropoWithMessageAndNumber(tropo_message, user.phone, type='text')

                error = False
                error_message = None
                message = 'Triggers for {}. OK'.format(user.name)
            else:
                error = True
                error_message = 'User not found'

    except Exception as e:
        traceback.print_exc()
    finally:
        output = {
            'error': error,
            'error_message': error_message,
            'message': message,
        }
    return Response(json.dumps(output), mimetype='application/json')


def replace_user_info_on_trigger_text(text, user):
    text = text.replace('{user.name}', str(user.name))
    text = text.replace('{user.phone}', str(user.phone))
    text = text.replace('{user.id}', str(user.id))
    return text


def replace_zone_information(text, zone):

    zone_name = zone.name
    if zone.vertical_name:
        zone_name = zone.vertical_name

    floor_name = zone.floor.name
    if zone.floor.vertical_name:
        floor_name = zone.floor.vertical_name

    text = text.replace('{zone.name}', zone_name)
    text = text.replace('{zone.id}', str(zone.id))
    text = text.replace('{zone.floor}', floor_name)
    return text


def get_engagement_triggers_per_zone(zone_id):
    output = []
    triggers = db_session.query(EngagementTrigger).filter(EngagementTrigger.zone_id == zone_id).all()

    for t in triggers:
        output.append(t)

    return output
