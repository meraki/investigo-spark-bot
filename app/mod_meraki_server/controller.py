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
from app import get_api_cmx
from app.models import CMXServer, Campus, Building, Floor, Zone, LocationSystem, MerakiServer, GPSMarker

mod_meraki_server = Blueprint('mod_meraki_server', __name__, url_prefix='/meraki_server')


@mod_meraki_server.route('/')
@mod_meraki_server.route('/show')
def show():
    try:
        servers = db_session.query(MerakiServer).all()
        return render_template("server/meraki_server/list.html", object=servers, deployment="Cloud")
    except:
        traceback.print_exc()
        return "No response"


@mod_meraki_server.route('/details/<server_id>')
def details(server_id):
    server = db_session.query(MerakiServer).filter(MerakiServer.id == server_id).first()
    return render_template("server/meraki_server/details.html", object=server, deployment="Cloud")


@mod_meraki_server.route('/edit/<server_id>')
def edit(server_id):
    return "Under construction"


@mod_meraki_server.route('/verticalization/<server_id>')
def verticalization(server_id):
    return "Under construction"


@mod_meraki_server.route('/delete/<server_id>', methods=['GET', 'POST'])
def delete(server_id):
    output = None
    try:
        server = db_session.query(MerakiServer).filter(MerakiServer.id == server_id).first()
        if request.method == 'GET':
            output = render_template("server/meraki_server/delete.html", object=server, deployment="Cloud")
        else:
            server = db_session.query(MerakiServer).filter(MerakiServer.id == request.form["meraki_server_id"]).delete()
            output = redirect(url_for('mod_meraki_server.show'))
    except:
        traceback.print_exc()
        output = redirect(url_for('error'))
        db_session.rollback()

    return output


# Set the route and accepted methods
@mod_meraki_server.route('/add', methods=['GET', 'POST'])
def add():
    output = {
        'error': None,
        'error_message': None,
        'redirect_url': None,
    }

    if request.method == 'GET':
        output = render_template("server/meraki_server/add.html", deployment="Cloud")

    else:
        try:
            if request.json:
                form_data = request.json
            else:
                form_data = request.form

            fake_server = form_data["fake_server"] == 'True'

            if fake_server:
                meraki_server = MerakiServer(name="Meraki HQ", active=True, organization_id=None, network_id=None, api_key=None, demo_server=True, demo_server_url="http://live-map.meraki.com/clients")
                valid_server = validate_meraki_server(meraki_server)
                output['error_message'] = valid_server

                if valid_server:
                    db_session.add(meraki_server)
                    db_session.commit()
                    output['redirect_url'] = url_for('mod_meraki_server.show')
                else:
                    output['error'] = True
                    output[
                        'error_message'] = 'There was an error setting up the Meraki Demo Server. Please check the data'
            else:
                output['error'] = True
                output['error_message'] = 'Under construction'

        except Exception as e:
            output['error'] = True
            output['error_message'] = str(e)
            db_session.rollback()
        output = Response(json.dumps(output), mimetype='application/json')

    return output


def validate_meraki_server(meraki_server):
    if meraki_server.demo_server:
        return setup_demo_server(meraki_server)
    else:
        return False


def setup_demo_server(meraki_server):
    output = False

    if meraki_server.name == "Meraki HQ" and "live-map.meraki.com" in meraki_server.demo_server_url:
        filename = "meraki/meraki-hq-san-francisco.json"

        try:
            filename = os.path.join(app.static_folder, 'server_config/{}'.format(filename))

            with open(filename) as data_file:
                server_info = json.load(data_file)

                db_session.query(Campus).delete()
                campuses = []
                counter_campus = 0

                meraki_location_system = LocationSystem(meraki_server.name)
                meraki_location_system.campuses = campuses
                meraki_server.location_system = meraki_location_system

                for campus in server_info["campuses"]:
                    counter_buildings = 0
                    counter_floors = 0
                    counter_zones = 0
                    counter_campus += 1
                    name = campus["name"]
                    campus_uid = campus["aesUid"]
                    output = True
                    campus_uid = campus["aesUid"]
                    db_campus = Campus(campus_uid, name, buildings=None)
                    campuses.append(db_campus)
                    db_campus.location_system = meraki_location_system
                    db_campus.location_system_id = meraki_location_system.id
                    db_session.add(db_campus)

                    server_buildings = campus["buildingList"]
                    if server_buildings:
                        for b in server_buildings:
                            counter_buildings += 1
                            name = b["name"]
                            building_uid = b["aesUid"]
                            object_version = b["objectVersion"]

                            db_building = Building(db_campus.aes_uid, building_uid, object_version, name, floors=None)
                            db_session.add(db_building)

                            server_floors = b["floorList"]
                            if server_floors:
                                for f in server_floors:
                                    counter_floors += 1
                                    name = f["name"]
                                    aes_uid = f["aesUid"]
                                    calibration_model_id = 0
                                    object_version = 0

                                    floor_length = f["dimension"]["length"]
                                    floor_width = f["dimension"]["width"]
                                    floor_height = f["dimension"]["height"]
                                    floor_offset_x = f["dimension"]["offsetX"]
                                    floor_offset_y = f["dimension"]["offsetY"]
                                    floor_unit = f["dimension"]["unit"]

                                    image_name = f["image"]["imageName"]
                                    image_zoom_level = f["image"]["zoomLevel"]
                                    image_width = f["image"]["width"]
                                    image_height = f["image"]["height"]
                                    image_size = f["image"]["size"]
                                    image_max_resolution = f["image"]["maxResolution"]
                                    image_color_depth = f["image"]["colorDepth"]

                                    treated_floor_name = ''.join(e for e in name if e.isalnum())

                                    #filename = os.path.join(app.static_folder, 'maps/meraki-hq/{}.png'.format(treated_floor_name))
                                    map_path = url_for('static', filename='maps/meraki-hq/{}.png'.format(treated_floor_name))


                                    db_floor = Floor(db_building.aes_uid, aes_uid, calibration_model_id, object_version,
                                                     name, floor_length, floor_width,
                                                     floor_height, floor_offset_x, floor_offset_y, floor_unit,
                                                     image_name, image_zoom_level, image_width,
                                                     image_height, image_size, image_max_resolution, image_color_depth, map_path=map_path)
                                    db_session.add(db_floor)
                                    server_zones = f["zones"]
                                    # skipping the zones for now

                                    server_gps_markers = f["gpsMarkers"]
                                    for gps_marker in server_gps_markers:
                                        gps_marker_name = gps_marker["name"]
                                        gps_marker_latitude = gps_marker["geoCoordinate"]["latitude"]
                                        gps_marker_longitude = gps_marker["geoCoordinate"]["longitude"]
                                        gps_marker_unit = gps_marker["geoCoordinate"]["unit"]

                                        db_gps_marker = GPSMarker(db_floor.aes_uid, gps_marker_name, gps_marker_latitude, gps_marker_longitude, gps_marker_unit)
                                        db_session.add(db_gps_marker)

                    print (
                    "{} has {} buildings, {} floors, {} zones".format(db_campus.name, counter_buildings, counter_floors,
                                                                      counter_zones))
                    output = True

        except Exception as e:
            traceback.print_exc()
            db_session.rollback()
            output = False

    return output

