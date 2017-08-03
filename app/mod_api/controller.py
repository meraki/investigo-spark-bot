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
import traceback, json, datetime
from flask import Blueprint, Response, url_for
from app.database import db_session, db_engine
from app import get_api_cmx
from app.mod_cmx_notification.models import CMXNotification
from app.mod_user.models import RegisteredUser
from app.models import DeviceLocation, Floor
from dateutil import parser

mod_api = Blueprint('mod_api', __name__, url_prefix='/api')
expiration_time = 5  # 5 seconds


@mod_api.route('/hierarchy/<hierarchy>')
@mod_api.route('/hierarchy')
def clients_hierarchy(hierarchy=None):
    output = {'error': None}
    try:
        output['items'] = get_devices_divided_by_hierarchy(use_asynchronous_data=True, hierarchy=hierarchy)
    except Exception as e:
        traceback.print_exc()
        output = format_error_dictionary(str(e))

    return Response(json.dumps(output), mimetype='application/json')


@mod_api.route('/overview')
def overview():
    output = {'error': None}
    try:
        output['hierarchies'] = get_devices_divided_by_hierarchy(use_asynchronous_data=True)

    except Exception as e:
        traceback.print_exc()
        output = format_error_dictionary(str(e))

    return Response(json.dumps(output), mimetype='application/json')


@mod_api.route('/client/<mac_address>')
def client(mac_address):
    output = {'error': None}
    try:
        output['items'] = get_device_location(mac_address, True)

    except Exception as e:
        traceback.print_exc()
        output = format_error_dictionary(str(e))

    return Response(json.dumps(output), mimetype='application/json')


@mod_api.route('/engagement/<hierarchy>/<mac_address>')
@mod_api.route('/engagement/<hierarchy>')
def engagement(hierarchy, mac_address=None):
    output = {}

    return json.dumps(output)


def get_device_location(mac_address, use_asynchronous_data=False):
    items = get_devices_and_users(mac_address=mac_address)
    registered_users = items['registered_users']
    unknown_devices = items['unknown_devices']
    if len(registered_users) == len(unknown_devices) == 0:
        try:
            info = get_api_cmx().get_client_information(mac_address)
            if info:
                item = {}
                location_info = None

                if 'mapHierarchyString' in info['mapInfo']:
                    hierarchy = info['mapInfo']['mapHierarchyString']
                    coord_x = info['mapCoordinate']['x']
                    coord_y = info['mapCoordinate']['y']
                    last_modified = info['statistics']['lastLocatedTime']
                    location_info = __serialize_location_information(coord_x, coord_y, hierarchy, last_modified, 'static')
                    user = db_session.query(RegisteredUser).filter(RegisteredUser.mac_address == mac_address).first()
                    if user:
                        item['user_info'] = __serialize_user_information(user.name, user.phone, user.id)
                        registered_users.append(item)
                    else:
                        unknown_devices.append(item)

                item['location'] = location_info

        except:
            traceback.print_exc()
            pass

    return items


def get_devices_and_users(mac_address=None, hierarchy=None, user_name=None, order_by=('location', 'hierarchy', 'ASC'), use_asynchronous_data=False):

    dl = DeviceLocation.__tablename__
    ru = RegisteredUser.__tablename__
    sql = "SELECT {}. mac_address as mac, {}.*, {}.* FROM {} LEFT JOIN {} ON {}.mac_address = {}.mac_address ".format(dl,dl, ru, dl, ru, dl, ru)

    any_filter = False
    if mac_address:
        clause = "{}.mac_address = '{}'".format(dl, mac_address)
        sql += ' WHERE ' + clause
        any_filter = True

    if hierarchy:
        clause = " {}.hierarchy LIKE '{}%%'".format(dl, hierarchy)
        if not any_filter:
            sql += ' WHERE ' + clause
        else:
            sql += ' AND ' + clause

    if order_by[0] == 'location':
        sql += ' ORDER BY {}.{} {}'.format(dl, order_by[1], order_by[2])

    elif order_by[0] == 'user':
        sql += ' ORDER BY {}.{} {}'.format(ru, order_by[1], order_by[2])

    result = db_engine.execute(sql)
    items = __serialize_devices_users(result)

    return items


def __filter_hierarchy(hierarchy_name, hierarchies, last_hierarchy=None):
    if last_hierarchy and last_hierarchy['name'] == hierarchy_name:
        output = last_hierarchy
    else:
        filtered_list = list(filter(lambda h: h['name'] == hierarchy_name, hierarchies))
        if len(filtered_list) > 0:
            output = filtered_list[0]
        else:
            output = None

    if not output:
        output = {
            'name': hierarchy_name,
            'unknown_devices': [],
            'registered_users': []
        }
        hierarchies.append(output)

    return output


def format_error_dictionary(error_message, error_code=None):
    output = {
        'error': {

            'code': error_code,
            'message': error_message
        }
    }
    return output


def get_devices_divided_by_hierarchy(use_asynchronous_data=True, hierarchy=None):
    items = get_devices_and_users()
    registered_users = items['registered_users']
    unknown_devices = items['unknown_devices']
    if use_asynchronous_data and len(registered_users) == 0 and len(unknown_devices) == 0:
        if len(registered_users) == len(unknown_devices) == 0:
            try:
                clients_information = get_api_cmx().get_clients_list()
                if clients_information:
                    for info in clients_information:
                        item = {}
                        location_info = None
                        currently_tracked = info['currentlyTracked']
                        mac_address = info['macAddress']
                        if currently_tracked and 'mapHierarchyString' in info['mapInfo']:
                            h = info['mapInfo']['mapHierarchyString']
                            coord_x = info['mapCoordinate']['x']
                            coord_y = info['mapCoordinate']['y']
                            last_modified = info['statistics']['lastLocatedTime']
                            location_info = __serialize_location_information(coord_x, coord_y, h, last_modified,
                                                                             'static')
                            user = db_session.query(RegisteredUser).filter(
                                RegisteredUser.mac_address == mac_address).first()
                            if user:
                                item['user_info'] = __serialize_user_information(user.name, user.phone, user.id)
                                registered_users.append(item)
                            else:
                                unknown_devices.append(item)
                        item['location'] = location_info
                        item['mac_address'] = mac_address
            except:
                traceback.print_exc()

    hierarchies = []
    current_hierarchy = None
    for i in items['registered_users']:
        current_hierarchy = __filter_hierarchy(i['location']['hierarchy'], hierarchies, current_hierarchy)
        current_hierarchy['registered_users'].append(i)

    for i in items['unknown_devices']:
        current_hierarchy = __filter_hierarchy(i['location']['hierarchy'], hierarchies, current_hierarchy)
        current_hierarchy['unknown_devices'].append(i)


    if hierarchy:
        try:
            hierarchies = __filter_hierarchy(hierarchy, hierarchies)
        except:
            hierarchies = []

    return hierarchies


def is_expired(last_modified):
    global expiration_time
    time_delta = datetime.datetime.now().replace(tzinfo=last_modified.tzinfo) - last_modified
    seconds_since_last_update = time_delta.total_seconds()
    return seconds_since_last_update > expiration_time


def is_time_to_update():
    output = True

    latest_movement = db_session.query(DeviceLocation).first()

    if latest_movement:
        output = is_expired(latest_movement.last_modified)

    return output


def too_many_notifications_rows(limit=1000):
    sql = "SELECT COUNT(*) as cnt FROM {};".format(CMXNotification.__tablename__)
    notifications_count_result = db_engine.execute(sql).first()
    count = notifications_count_result[0]
    return count > limit


def update_tables():
    sql = "SELECT DISTINCT ON (mac_address) * " \
     "FROM   {} " \
     "ORDER  BY mac_address DESC, " \
     "          timestamp DESC;".format(CMXNotification.__tablename__) \

    notifications_result = db_engine.execute(sql)

    for row in notifications_result:
        mac_address = row['mac_address']
        hierarchy = row['location_map_hierarchy']
        coord_x = row['location_x']
        coord_y = row['location_y']
        notification_type = row['notification_type']
        db_session.query(DeviceLocation).filter(DeviceLocation.mac_address == mac_address).delete()
        if notification_type == 'locationupdate':
            location = DeviceLocation(mac_address, hierarchy, datetime.datetime.now(), coord_x, coord_y)
            db_session.add(location)
    db_session.query(CMXNotification).delete()
    db_session.commit()


@mod_api.before_request
def before_request():
    if is_time_to_update():
        update_tables()


def __serialize_devices_users(result):
    unknown_devices = []
    registered_users = []

    for row in result:
        item = {}

        item['location'] = __serialize_location_information(row['coord_x'], row['coord_y'], row['hierarchy'], row['last_modified'], 'notification')
        item['mac_address'] = row['mac']

        if (row['name']):
            user_info = {}
            item['user_info'] = __serialize_user_information(row['name'], row['phone'], row['id'])
            registered_users.append(item)
        else:
            unknown_devices.append(item)

    output = {
        'unknown_devices': unknown_devices,
        'registered_users': registered_users
    }
    return output


def __serialize_location_information(coord_x, coord_y, hierarchy, last_modified, origin):
    last_modified_ago = __calculate_time_ago (last_modified)
    output = {
        'coord_x': str(coord_x),
        'coord_y': str(coord_y),
        'hierarchy': str(hierarchy),
        'last_modified': str(last_modified),
        'last_modified_ago':  last_modified_ago,
        'map_information': __get_map_information(hierarchy),
        'origin': origin
        }
    return output


def __get_map_information(hierarchy):
    hierarchies = hierarchy.split(">")
    floor_name = hierarchies[2].strip()
    floor = db_session.query(Floor).filter(Floor.name == floor_name).first()
    if floor:
        output = {
            'map_path': str(floor.map_path),
            'floor_width': str(floor.floor_width),
            'floor_height': str(floor.floor_height),
            'floor_length': str(floor.floor_length),
            'image_width': str(floor.image_width),
            'image_height': str(floor.image_height)
        }
    else:
        output = None
    return output


def __serialize_user_information(name, phone, id):
    output = {
        'name': name,
        'phone': phone,
        'id': id,
    }
    return output


def display_time(seconds, granularity=2):
    intervals = (
        ('weeks', 604800),  # 60 * 60 * 24 * 7
        ('days', 86400),  # 60 * 60 * 24
        ('hours', 3600),  # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
    )
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append("{} {}".format(value, name))
    return ', '.join(result[:granularity])


def __calculate_time_ago(last_modified):
    if not isinstance(last_modified, datetime.datetime):
        last_modified = parser.parse(last_modified)
    now = datetime.datetime.now(tz=last_modified.tzinfo)
    last_modified_ago = display_time((now - last_modified).total_seconds())
    return last_modified_ago