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
import traceback
import json
from flask import Blueprint, render_template, redirect, request, url_for

from app.database import db_session
from app.mod_api import controller as api_module
from app import get_controller
from app.models import Floor

mod_monitor = Blueprint('mod_monitor', __name__, url_prefix='/monitor')


@mod_monitor.route('/overview/')
def overview():
    data = get_controller().get_hierarchies_serialized()
    #print (json.dumps(data, indent=2))
    return render_template('monitor/show/overview_show.html', data=data)


@mod_monitor.route('/device/select', methods=['GET', 'POST'])
def device_select():
    data = api_module.get_devices_and_users(order_by=('location', 'last_modified', 'DESC'))

    if request.method == 'GET':
        output = render_template('monitor/select/device_select.html', data=map(json.dumps, data))
    else:
        mac_address = request.form["mac"]
        url = url_for('.device_show', mac=mac_address)
        output = redirect(url)
    return output


@mod_monitor.route('/device/<mac>')
@mod_monitor.route('/device')
def device_show(mac=None):
    data = {'error': None,
            'items': None
            }
    try:
        items = api_module.get_device_location(mac, use_asynchronous_data=True)

        data['items'] = items
    except Exception as e:
        data = {'error': True,
                'error_message': str(e)
                }
        traceback.print_exc()
    return render_template('monitor/show/device_show.html', data=data, mac_address=mac)


@mod_monitor.route('/hierarchy/select', methods=['GET', 'POST'])
def hierarchy_select():
    if request.method == 'GET':
        floors = db_session.query(Floor).all()
        output = render_template('monitor/select/hierarchy_select.html', floors=floors)
    else:
        hierarchy = request.form["hierarchy"]
        url = url_for('.hierarchy_show', hierarchy=hierarchy)
        output = redirect(url)

    return output


@mod_monitor.route('/hierarchy/<hierarchy>')
def hierarchy_show(hierarchy):
    output = render_template('monitor/show/hierarchy_show.html', hierarchy=hierarchy)
    return output