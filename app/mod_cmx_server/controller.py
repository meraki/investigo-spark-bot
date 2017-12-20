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
from app.models import CMXServer, Campus, Building, Floor, Zone, LocationSystem

mod_cmx_server = Blueprint('mod_cmx_server', __name__, url_prefix='/cmx_server')


@mod_cmx_server.route('/')
@mod_cmx_server.route('/show')
def show():
    try:
        servers = db_session.query(CMXServer).all()
        return render_template("server/cmx_server/list.html", object=servers, deployment="On-premises")

    except:
        traceback.print_exc()
        return "No response"


@mod_cmx_server.route('/details/<server_id>')
def details(server_id):
    server = db_session.query(CMXServer).filter(CMXServer.id == server_id).first()
    return render_template("server/cmx_server/details.html", object=server, deployment="On-premises")


# Set the route and accepted methods
@mod_cmx_server.route('/add', methods=['GET', 'POST'])
def add():
    output = {
        'error': None,
        'error_message': None,
        'redirect_url': None,
    }
    if request.method == 'GET':
        output = render_template("server/cmx_server/add.html", deployment="On-premises")

    else:
        try:
            if request.json:
                form_data = request.json
            else:
                form_data = request.form
            name = form_data["cmx_server_name"]
            url = form_data["cmx_server_url"]
            username = form_data["cmx_server_username"]
            password = form_data["cmx_server_password"]
            externally_accessible = form_data["cmx_server_externally_accessible"] == 'True'
            active = form_data["cmx_server_active"] == 'True'

            cmx_server = CMXServer(name, url, username, password, active, externally_accessible)

            valid_server = validate_cmx_server(cmx_server)

            if valid_server:
                if active:
                    elect_active_server()

                db_session.add(cmx_server)
                db_session.commit()
                output['redirect_url'] = url_for('mod_cmx_server.show')
            else:
                output['error'] = True
                output['error_message'] = 'There was an error on the communication with the cmx_server. Please check the data'

        except Exception as e:
            output['error'] = True
            output['error_message'] = str(e)
            db_session.rollback()
        output = Response(json.dumps(output), mimetype='application/json')

    return output


@mod_cmx_server.route('/edit/<server_id>', methods=['GET', 'POST'])
def edit(server_id):
    output = None
    try:
        server = db_session.query(CMXServer).filter(CMXServer.id == server_id).first()
        if request.method == 'GET':
            output = render_template("server/cmx_server/edit.html", object=server, deployment="On-premises")
        else:
            server.name = request.form["cmx_server_name"]
            server.externally_accessible = request.form["cmx_server_externally_accessible"] == 'True'
            db_session.commit()
            output = redirect(url_for('mod_cmx_server.show'))

    except Exception as e:
        traceback.print_exc()
        output = redirect(url_for('mod_error.home', message=str(e)))
        db_session.rollback()
    return output


@mod_cmx_server.route('/verticalization/<server_id>', methods=['GET'])
def verticalization(server_id):
    output = None
    try:
        server = db_session.query(CMXServer).filter(CMXServer.id == server_id).first()
        output = render_template("server/verticalization.html", object=server, deployment="On-premises")

    except Exception as e:
        traceback.print_exc()
        output = redirect(url_for('mod_error.home', message=str(e)))
        db_session.rollback()
    return output



@mod_cmx_server.route('/verticalization/add/<server_id>', methods=['POST'])
def verticalization_add(server_id):
    output = {
        'error': None,
        'error_message': None,
        'redirect_url': None,
    }
    try:
        form_json = request.json

        vertical = None
        language = None

        vertical = form_json['vertical']
        if vertical.lower() not in ["healthcare", 'retail']:
            vertical = None

        language = form_json['language']
        if language.lower() not in ["english", 'portuguese']:
            language = None

        if not vertical:
            vertical = 'Retail'

        if not language:
            language = 'English'


        json_vertical_names_file = os.path.join(app.static_folder, 'server_config/verticalization.json')

        with open(json_vertical_names_file) as data_file:
            verticals = json.load(data_file)

        vertical_names = None
        for v in verticals:
            if v['vertical'].lower() == vertical.lower():
                items = v['items']
                for item in items:
                    if language.lower() == item['language'].lower():
                        vertical_names = item['vertical_names']
                        break

        cmx_location_system = db_session.query(LocationSystem).filter(LocationSystem.id == server_id).first()
        campi = cmx_location_system.campuses
        counter_campus = 0
        counter_floor = 0
        counter_building = 0
        counter_zone = 0
        campi_names = vertical_names['campi']
        buildings_names = vertical_names['buildings']
        floors_names = vertical_names['floors']
        zones_names = vertical_names['zones']

        for campus in campi:
            campus.vertical_name = campi_names[counter_campus % len(campi_names)]
            counter_campus += 1
            for building in campus.buildings:
                building.vertical_name = buildings_names[counter_building % len(buildings_names)]
                counter_building += 1
                for floor in building.floors:
                    floor.vertical_name = floors_names[counter_floor % len(floors_names)]
                    counter_floor += 1
                    for zone in floor.zones:
                        zone.vertical_name = zones_names[counter_zone % len(zones_names)]
                        counter_zone += 1
                        key_occupancy = '{}_occupancy'.format(zone.id)
                        if key_occupancy in form_json:
                            max_occupation = form_json[key_occupancy]
                            if max_occupation >= 0:
                                zone.max_occupation = max_occupation
                        else:
                            raise Exception('Missing information for {}'.format(zone.name))

        db_session.commit()
        output['redirect_url'] = url_for('mod_cmx_server.details', server_id=server_id)
    except Exception as e:
        output['error'] = True
        output['error_message'] = str(e)
        traceback.print_exc()
        db_session.rollback()

    output = Response(json.dumps(output), mimetype='application/json')
    return output


@mod_cmx_server.route('/delete/<server_id>', methods=['GET', 'POST'])
def delete(server_id):
    output = None
    try:
        server = db_session.query(CMXServer).filter(CMXServer.id == server_id).first()
        if request.method == 'GET':
            output = render_template("server/cmx_server/delete.html", object=server, deployment="On-premises")
        else:
            server = db_session.query(CMXServer).filter(CMXServer.id == request.form["cmx_server_id"]).delete()
            output = redirect(url_for('mod_cmx_server.show'))
    except:
        traceback.print_exc()
        output = redirect(url_for('error'))
        db_session.rollback()

    return output


def elect_active_server(active_server_id=None):
    if active_server_id:
        db_session.query(CMXServer).filter(CMXServer.id != active_server_id).update({"active": False})
    else:
        db_session.query(CMXServer).update({"active": False})


def download_floor_images(api):
    output = True
    zones = db_session.query(Zone).all()
    print (zones)
    floors = db_session.query(Floor).all()
    print ('Downloading images from {} floors'.format(len(floors)))
    for floor in floors:
        try:
            treated_floor_name = ''.join(e for e in floor.name if e.isalnum())
            filename = os.path.join(app.static_folder, 'maps/{}.png'.format(treated_floor_name))

            response = api.download_hierarchy_image(floor.image_name)
            with open(filename,  'w+') as fo:
                fo.write(response.content)
                fo.close()
                floor.map_path = url_for('static', filename="maps/{}.png".format(treated_floor_name))
        except:
            traceback.print_exc()
            print ('Could not download image for {}'.format(floor.name))

    return output


def validate_cmx_server(cmx_server):
    output = True
    api = get_api_cmx(cmx_server)
    # TODO get servers timezone and add it to db (would have to create another column on the table)
    server_info = None
    try:
        server_info = api.get_all_maps()
    except:
        file_path = None
        filename = None
        url = cmx_server.url
        if 'msesandbox.cisco.com:8081' in url:
            filename = 'DevNet.json'
        elif '10.97.40.43' in url or '10.97.20.218' in url:
            # TODO get file path for JSON that contains CENU info
            filename = 'CENU.json'

        if filename:
            filename = os.path.join(app.static_folder, 'server_config/{}'.format(filename))

            with open(filename) as data_file:
                server_info = json.load(data_file)

    if server_info:
        try:
            db_session.query(Campus).delete()
            campuses = []
            counter_campus = 0
            cmx_location_system_name = cmx_server.name
            cmx_location_system = LocationSystem(cmx_location_system_name)
            cmx_location_system.campuses = campuses
            cmx_server.location_system = cmx_location_system
            for campus in server_info["campuses"]:
                counter_buildings = 0
                counter_floors = 0
                counter_zones = 0
                counter_campus += 1
                name = campus["name"]
                campus_uid = campus["aesUid"]
                db_campus = Campus(campus_uid, name, buildings=None)
                campuses.append(db_campus)
                db_campus.location_system = cmx_location_system
                db_campus.location_system_id = cmx_location_system.id
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
                                calibration_model_id = f["calibrationModelId"]

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

                                db_floor = Floor(db_building.aes_uid, aes_uid, calibration_model_id, object_version, name, floor_length, floor_width,
                                                 floor_height, floor_offset_x, floor_offset_y, floor_unit, image_name, image_zoom_level, image_width,
                                                 image_height, image_size, image_max_resolution, image_color_depth)
                                db_session.add(db_floor)
                                server_zones = f["zones"]
                                if server_zones:
                                    for z in server_zones:
                                        counter_zones += 1
                                        name = z["name"]
                                        zone_type = z["zoneType"]
                                        coordinates = z["zoneCoordinate"]
                                        zone_xs = []
                                        zone_ys = []
                                        zone_zs = []
                                        for coordinate in coordinates:
                                            zone_xs.append(coordinate["x"])
                                            zone_ys.append(coordinate["y"])
                                            zone_zs.append(coordinate["z"])

                                        zone_center_x = sum(zone_xs) / len(zone_xs)
                                        zone_center_y = sum(zone_ys) / len(zone_ys)
                                        zone_center_z = sum(zone_zs) / len(zone_zs)
                                        db_zone = Zone(db_floor.aes_uid, name, zone_type, zone_center_x, zone_center_y, zone_center_z)
                                        db_session.add(db_zone)




                print ("{} has {} buildings, {} floors, {} zones".format(db_campus.name, counter_buildings, counter_floors,
                                                                  counter_zones))

            output = download_floor_images(api)

        except:
            traceback.print_exc()
            output = False
    else:
        output = False

    return output



@mod_cmx_server.route('/verticalization/remove/<server_id>', methods=['POST'])
def verticalization_remove(server_id):
    output = {
        'error': None,
        'error_message': None,
        'redirect_url': None,
    }
    try:
        form_json = request.json
        location_system = db_session.query(LocationSystem).filter(LocationSystem.id == server_id).first()
        campi = location_system.campuses
        for campus in campi:
            campus.vertical_name = None
            for building in campus.buildings:
                building.vertical_name = None
                for floor in building.floors:
                    floor.vertical_name = None
                    for zone in floor.zones:
                        zone.vertical_name = None
                        zone.max_occupation = -1
        db_session.commit()
        output['redirect_url'] = url_for('mod_cmx_server.details', server_id=server_id)
    except Exception as e:
        output['error'] = True
        output['error_message'] = str(e)
        traceback.print_exc()
        db_session.rollback()

    output = Response(json.dumps(output), mimetype='application/json')
    return output
