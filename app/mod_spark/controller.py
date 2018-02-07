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
from ciscosparkapi.api.messages import Message
from flask import Blueprint, request, url_for
import traceback
import json
import os
import datetime
from app import app
from app import get_api_spark, get_api_tropo, get_notification_sms_phone_number, get_sms_enabled, get_admin_name, get_show_web_link
from app.database import db_session
from app.mod_statistics.models import SparkCommandRequest
from app.mod_user.models import RegisteredUser
from app.mod_api.controller import get_device_location, get_devices_divided_by_hierarchy
import plotly.plotly as py
import plotly.graph_objs as go
import math

from app.models import Floor, Zone

py.sign_in('rafacarv', 'zMrWUiu61ulJhbKBLSSV')
import re
from sqlalchemy import func
from app import get_controller_status
from app.mod_statistics.models import SparkCommandRequest

mod_spark = Blueprint('mod_spark', __name__, url_prefix='/spark')

@mod_spark.route('/webhook', methods=['GET', 'POST'])
def home():
    output = "Empty"
    try:
        # print(json.dumps(request.json, indent=2))
        parsed_input = parse_user_input(request)

        message = parsed_input
        room_id_received_on_message = message.roomId

        # this logs the message on the console
        print ("Received: {}".format(message.text))

        # print("Mentioned people - {}".format(message.mentionedPeople))
        # Here you will analyze all the messages received on the room and react to them
        message_text = message.text


        if message.mentionedPeople:
            for person_id in message.mentionedPeople:
                person = get_api_spark().people.get(person_id)
                target = person.displayName
                # print ('Looking for {} on {}'.format(target, message_text))
                new_message_text = message_text.replace(target, '', 1).strip()

                # print ('Result = {}'.format(new_message_text))

                if new_message_text == message_text:
                    target = person.displayName.split(' ')[0]
                    # print ('Looking for {} on {}'.format(person.displayName.split(' ')[0], new_message_text))
                    new_message_text = message_text.replace(target, '', 1).strip()
                    # print ('Result = {}'.format(new_message_text))

                message_text = new_message_text

        first_word = message_text.lower().strip()

        command_category = 'unrecognized'

        if first_word.startswith('find'):
            output = command_find(message_text, message.roomId, message.personId)
            command_category = 'find'

        elif first_word.startswith('list'):
            output = command_list(message_text, message.roomId, message.personId)
            command_category = 'list'

        elif first_word.startswith('add'):
            output = command_add(message_text, message.roomId, message.personId)
            command_category = 'add'

        elif first_word.startswith('help'):
            output = command_help(message.roomId)
            command_category = 'help'

        if not output:
            output = 'Command not identified'
            write_to_spark(room_id=room_id_received_on_message, text=output)
            command_category = 'unrecognized'


        log_command(command_category, message.id, message.roomId, message.personId, message.personEmail, message.created, message.roomType, message_text, get_controller_status())


    except Exception as e:
        traceback.print_exc()
        output = str(e)

    return output


def log_command(command_category, message_id, room_id, person_id, person_email, created, room_type, message_text, deployment_status):
    #instantiate new spark_command

    try:
        spark_command_request = SparkCommandRequest(message_id, command_category, room_id, person_id, person_email, created, room_type, message_text, deployment_status)
        db_session.add(spark_command_request)
        db_session.commit()

    except Exception as e:
        db_session.rollback()
        traceback.print_exc()
        print ("Error while trying to log the command")


def command_list(message_text, room_id, person_id):
    second_word = __replace_string_case_insensitive(message_text, 'list', '').strip().lower()
    post_markdown = None
    post_text = None

    if second_word in ['users', 'user', 'asset', 'assets']:
        users = db_session.query(RegisteredUser).all()

        post_text = '{} items were found:'.format(len(users))
        post_markdown = "# {}\n".format(post_text)

        user_names = []
        for user in users:
            user_names.append(user.name)
            post_markdown += '{}. {} ({})\n'.format(len(user_names), user.name, user.mac_address)

        post_text += ' {}'.format(user_names)
    elif second_word in ['device', 'devices']:

        overview = get_devices_divided_by_hierarchy()
        """

        post_text = '{} items were found:'.format(len(users))
        post_markdown = "# {}\n".format(post_text)

        user_names = []
        for user in users:
            user_names.append(user.name)
            post_markdown += '{}. {} ({})\n'.format(len(user_names), user.name, user.mac_address)

        post_text += ' {}'.format(user_names)
        """

        count = 0

        for hierarchy in overview:
            count += len(hierarchy["unknown_devices"])

        # this line below takes the first device of each hierarchy and adds to the list
        devices = [item["unknown_devices"][0]['mac_address'] for item in overview]

        post_text = "{} unknown devices and were found. Here's a sample:".format(count)
        post_markdown = "# {}\n".format(post_text)

        for i in range(len(devices)):
            post_markdown += '{}. {}\n'.format(i, devices[i])

        post_text += ' {}'.format(devices)

    else:
        post_text = 'Invalid list command. Try list users/assets or list devices'
    print ('Posting on Spark... {}'.format(post_text))
    write_to_spark(room_id, None, None, post_text, post_markdown, None)

    return post_text


def command_add(message_text, room_id, person_id):
    post_text = 'Command not valid... Usage = add user/asset name MAC_address phone[optional]'
    try:
        message_pieces = message_text.split(' ')
        second_word = message_pieces[1].lower()
        if second_word in ['user', 'asset', 'user/asset']:
            name = message_pieces[2]
            mac_address = message_pieces[3]
            phone = None
            if len(message_pieces) > 4:
                phone = message_pieces[3]

            try:
                user = RegisteredUser(name, mac_address, phone)
                db_session.add(user)
                db_session.commit()
                post_text = 'Item created successfully'
            except Exception as e:
                if 'duplicate key value violates unique constraint "registered_user_mac_address_key"' in str(e):
                    post_text = 'MAC Address already registered. Try a different value'
                else:
                    post_text = str(e)
                db_session.rollback()
    except:
        pass

    finally:
        print ('Posting on Spark... {}'.format(post_text))
        write_to_spark(room_id, None, None, post_text, None, None)

    return post_text


def command_help(room_id):
    try:
        post_text = 'Available commands: "help"; "list assets"; "find asset [asset_name]"; "find asset [mac_address]"'
        post_markdown = """        
# Hi! My name is Investigo. Nice to meet you!
Here is a list of things I can do:

+ **list assets**: gives a list of registered assets;
+ **find asset _[asset_name]_**: finds the asset based on its name;
+ **find _[mac_address]_**: finds the asset based on its MAC Address;

Examples:

> list assets

> find asset defibrillator

> find 00:00:2a:01:00:32        
"""
    finally:
        print ('Posting on Spark... {}'.format(post_text))
        write_to_spark(room_id, None, None, post_text, post_markdown, None)

    return post_text


def command_find(message_text, room_id, person_id):
    try:

        success = False

        post_to_person_id = None  #
        post_to_person_email = None
        post_text = None
        post_markdown = None
        post_files = None
        post_room_id = room_id

        user_name = None

        message_text = message_text.replace('find', '').strip()

        message_text = __replace_string_case_insensitive(message_text, 'find', '').strip()

        mac = None

        if message_text.startswith('user') or message_text.startswith('asset'):
            content = message_text.replace('user', '').replace('asset', '').strip()
            user = db_session.query(RegisteredUser).filter(func.lower(RegisteredUser.name) == func.lower(content)).first()

            if user:
                mac = user.mac_address
                user_name = user.name
            else:
                post_text = "I am sorry. I could not find any user named {}".format(content)

        else:
            mac = message_text

        if mac:
            location = get_device_location(mac, True)
            # print(json.dumps(location, indent=2))
            location = location['unknown_devices'] + location['registered_users']
            # print location[0]
            if len(location) > 0 and location[0]['location']:

                location = location[0]['location']
                map_path = location['map_information']['map_path']
                background_image_path = url_for('static', filename=map_path.replace('/static/', ''), _external=True)
                #print (background_image_path)
                #background_image_path = 'http://cmx-investigo.herokuapp.com' + map_path
                #print background_image_path
                destination_x = int(math.floor(float(location['coord_x'])))
                destination_y = int(math.floor(float(location['coord_y'])))
                image_width = float(location['map_information']['image_width'])
                image_height = float(location['map_information']['image_height'])
                floor_width = float(location['map_information']['floor_width'])
                floor_length = float(location['map_information']['floor_length'])
                #local_file = plot_point_over_image(background_image_path, coord_x, coord_y, image_width, image_height, floor_width, floor_length)

                hierarchies = location['hierarchy']
                last_modified_ago = location['last_modified_ago']
                if (last_modified_ago == ' ' or last_modified_ago == ''):
                    last_modified_ago = '0 seconds'

                # image_path = url_for('static', filename=local_file, _external=True)

                # post_files = ['http://static.dnaindia.com/sites/default/files/2015/09/15/373721-wikipedia1.png']
                post_text = 'Device is at {}. Coordinates: ({}, {}). Information obtained {} ago'.format(
                    location['hierarchy'], destination_x, destination_y, location['last_modified_ago'])

                split_hierarchies = hierarchies.split('>')
                campus_name = split_hierarchies[0]
                building_name = split_hierarchies[1]
                floor_name = split_hierarchies[2]
                zone_name = None

                combined_hierarchies = '{}>{}>{}'.format(campus_name, building_name, floor_name)
                if len(split_hierarchies) > 3:
                    zone_name = split_hierarchies[3]
                    combined_hierarchies += '>{}'.format(zone_name)

                floor = db_session.query(Floor).filter(Floor.name == floor_name).first()
                if floor.vertical_name:
                    floor_name = floor.vertical_name
                    building_name = floor.building.vertical_name
                    campus_name = floor.building.campus.vertical_name
                    if zone_name:
                        zone = db_session.query(Zone).filter(Zone.name == zone_name).first()
                        if zone:
                            if zone.vertical_name:
                                zone_name = zone.vertical_name
                        else:
                            zone_name = None

                combined_hierarchies = '{}>{}>{}'.format(campus_name, building_name, floor_name)
                if zone_name:
                    combined_hierarchies += '>{}'.format(zone_name)

                origin_zone = floor.zones.first() # For the sake of the demo, I am positioning the requester on the first zone of the current floor

                if origin_zone:
                    origin_x = int(math.floor(origin_zone.zone_center_x))
                    origin_y = int(math.floor(origin_zone.zone_center_y))
                else:
                    # If floor where the device is located does not have any zones, we will use the central point.
                    origin_x = int(floor_width / 2)
                    origin_y = int(floor_length / 2)

                distance = int(math.floor(math.hypot(destination_x - origin_x, destination_y - origin_y)))

                post_markdown = "# The device has been found!\n"
                post_markdown += "Check attached map and the information below:\n"
                if user_name:
                    post_markdown += '+ **Name**: {}\n'.format(user_name)
                post_markdown += '+ **Distance**: {} feet\n'.format(distance)


                post_markdown += '+ **Campus**: {}\n'.format(campus_name)
                post_markdown += '+ **Building**: {}\n'.format(building_name)
                post_markdown += '+ **Floor**: {}\n'.format(floor_name)

                if zone_name:
                    post_markdown += '+ **Zone**: {}\n'.format(zone_name)
                post_markdown += '+ **Last seen**: {} ago\n'.format(last_modified_ago)
                #post_markdown += '+ **Coordinates**: ({}, {})\n'.format(destination_x, destination_y)
                if get_show_web_link():
                    if user_name:
                        post_markdown += '\n \n_The staff has been notified to pick it up. Click [here]({}) for live tracking._'.format(url_for('mod_monitor.device_show', mac=mac, _external=True))
                    else:
                        post_markdown += '\n \n_Click [here]({}) for live tracking._'.format(
                            url_for('mod_monitor.device_show', mac=mac, _external=True))

                local_file = \
                plot_origin_and_destination_over_image(background_image_path, origin_x, origin_y, destination_x,
                                                       destination_y, image_width, image_height, floor_width, floor_length, distance)[0]

                post_files = [local_file]
                success = True

            else:
                post_text = 'Device not found'

        if post_text is not None or post_markdown is not None:
            if success and user_name and get_sms_enabled():
                person = get_api_spark().people.get(person_id)
                if person.displayName == get_admin_name():
                    tropo_text = 'Please bring {} to Dr. {}. It is located at {}'.format(user_name, person.displayName, combined_hierarchies)#, url_for('mod_monitor.device_show', mac=mac, _external=True))
                    get_api_tropo().triggerTropoWithMessageAndNumber(tropo_text, get_notification_sms_phone_number(), type='text')
            print ('Posting on Spark... {}'.format(post_text))
            write_to_spark(post_room_id, post_to_person_id, post_to_person_email, post_text, post_markdown, post_files)
            if post_files:
                os.remove(post_files[0])
    except:
        post_text = 'An unexpected error occurred. Please try again in a few moments.'
        traceback.print_exc()
    return post_text


def parse_user_input(req):
    """Helper function to parse the information received by spark."""
    http_method = None

    if req.method == "GET":
        fake_json = {
          "roomType": "direct",
          "created": "2016-12-02T23:27:30.199Z",
          "personId": "Y2lzY29zcGFyazovL3VzL1BFT1BMRS82NmVjMDkyNi0zOTUxLTRkMDUtYWRlMC00YWIxOGZmMzQwZGE",
          "text": req.args["message"],
          "personEmail": "rafacarv@cisco.com",
          "roomId": "Y2lzY29zcGFyazovL3VzL1JPT00vZGFkYWIwZDAtZWEzMS0zNzU3LWJhOWQtNjMxZTVkOTc2YmU2",
          "id": "Y2lzY29zcGFyazovL3VzL01FU1NBR0UvZTRjY2JhNzAtYjhlNi0xMWU2LTkxNTktN2Q4NWUzOWFjYTc0"
        }
        output = Message(fake_json)

    elif req.method == "POST":
        # Get the json data from HTTP request. This is what was written on the Spark room, which you are monitoring.
        request_json = req.json
        message_id = request_json["data"]["id"]
        #print (json.dumps(request_json, indent=2))
        #print (message_id)
        # At first, Spark does not give the message itself, but it gives the ID of the message. We need to ask for the content of the message
        message = read_from_spark(message_id)
        output = message
    return output


def read_from_spark(message_id):
    try:
        spark_api = get_api_spark()
        message = spark_api.messages.get(message_id)
    except:
        traceback.print_exc()
        raise Exception("Error while trying to READ from Spark.")
    return message


def write_to_spark(room_id, to_person_id, to_person_email, text, markdown, files):
    try:
        if room_id != "FAKE":
            return get_api_spark().messages.create(files=files, roomId=room_id, text=text, markdown=markdown)
    except:
        traceback.print_exc()
        raise Exception("Error while trying to WRITE to Spark.")


@mod_spark.route('/plot', methods=['GET'])
def plot():

    #html = '<a href="{}">{}</a>'.format(path, path)
    background_image_path = 'http://cmx-investigo.herokuapp.com/static/maps/DevNetZone.png'
    origin_x = 107
    origin_y = 18

    destination_x = origin_x + 100
    destination_y = origin_y + 50

    floor_length = 81.9
    floor_width = 307.0
    image_height = 544.0
    image_width = 2038.0


    output = plot_origin_and_destination_over_image(background_image_path, origin_x, origin_y, destination_x, destination_y, image_width, image_height, floor_width, floor_length)
    #path = url_for('static', filename=filename, _external=True)
    #print (filename)

    html = '<img src="{}" />'.format(output[1])
    return html


def __replace_string_case_insensitive(string, find, replace):
    insensitive_hippo = re.compile(re.escape(find), re.IGNORECASE)
    return insensitive_hippo.sub(replace, string)


def plot_point_over_image(background_image_path, coord_x, coord_y, image_width, image_height, floor_width, floor_length):
    #plot_x = coord_x * image_width / floor_width
    #plot_y = coord_y * image_height / floor_length
    plot_x = math.floor((image_width / floor_width) * coord_x)
    plot_y = math.floor((image_height / floor_length) * coord_y)

    plot_x = coord_x
    plot_y = coord_y
    #print('({},{})'.format(plot_x, plot_y))


    marker_size = 0.02 * max(image_width, image_height)
    trace1 = go.Scatter(
        x=[coord_x],
        y=[coord_y],
        #mode='markers+text',

        #text=['Current position'],
        #textposition='top',
        mode='markers',
        marker=dict(
            size=marker_size,
            symbol='x-open',
            color='rgb(255,255,0)',
            line=dict(
                width=marker_size/10,
                color='rgb(0, 0, 0)'
            )
        )
    )
    layout = go.Layout(
        width=image_width,
        height=image_height,
        #https://plot.ly/python/axes/
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            autotick=True,
            ticks='',
            showticklabels=False,
            range=[0, floor_width],

        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            autotick=True,
            ticks='',
            showticklabels=False,
            range=[floor_length, 0],
        ),
        plot_bgcolor='transparent',
        paper_bgcolor='transparent',
        # https://plot.ly/python/reference/#layout-images
        images=[dict(
        # source="https://images.plot.ly/language-icons/api-home/python-logo.png",
        #source="http://cmx-investigo.herokuapp.com/static/maps/DevNetZone.png",
        source=background_image_path,
        xref="paper",
        yref="paper",
        xanchor='left',
        yanchor='bottom',
        x=0,
        y=0,
        sizex=1,
        sizey=1,
        sizing="stretch",
        opacity=1,
        layer="below")])
    fig = go.Figure(data=[trace1], layout=layout)
    file_path = 'maps_temp/cmx_finder-{}.png'.format(datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"))
    saved_file_name = os.path.join(app.static_folder, file_path)
    #print(saved_file_name)
    py.image.save_as(fig, saved_file_name)
    return saved_file_name


def plot_origin_and_destination_over_image(background_image_path, origin_x, origin_y, destination_x, destination_y, image_width, image_height, floor_width, floor_length, distance, text_origin='You are here', text_destination='Asset location'):

    annotation_x = ((origin_x + destination_x)/2)
    annotation_y = ((origin_y + destination_y)/2)

    marker_size = 0.02 * max(image_width, image_height)

    trace1 = go.Scatter(
        x=[origin_x, destination_x],
        y=[origin_y, destination_y],
        text=[text_origin, text_destination],
        textposition='bottom center',
        textfont=dict(
                    family='Courier New, monospace',
                    size=16,
                    color='#ffffff'
                ),
        mode='lines+markers+text',
        marker=dict(
            size=marker_size,
            symbol=['circle', 'x'],
            color=['red', 'yellow'],
            line=dict(
                width=marker_size/10,
                color='rgb(0, 0, 0)'
            )
        ),
        line=dict(
            width=marker_size / 10,
            color='blue'
        ),

    )
    layout = go.Layout(
        width=image_width,
        height=image_height,
        #https://plot.ly/python/axes/
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            autotick=True,
            ticks='',
            showticklabels=False,
            range=[0, floor_width],

        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            autotick=True,
            ticks='',
            showticklabels=False,
            range=[floor_length, 0],
        ),
        plot_bgcolor='transparent',
        paper_bgcolor='transparent',
        annotations=[
            dict(
                x=annotation_x,
                y=annotation_y,
                xref='x',
                yref='y',
                text='Distance = {} feet'.format(distance),

                font=dict(
                    family='Courier New, monospace',
                    size=16,
                    color='#ffffff'
                ),
                align='center',
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='#636363',
                #ax=20,
                # ay=-30,
                bordercolor='#c7c7c7',
                borderwidth=2,
                borderpad=4,
                bgcolor='#ff7f0e',
                opacity=0.8
            )
        ],
        # https://plot.ly/python/reference/#layout-images
        images=[dict(
        # source="https://images.plot.ly/language-icons/api-home/python-logo.png",
        #source="http://cmx-investigo.herokuapp.com/static/maps/DevNetZone.png",
        source=background_image_path,
        xref="paper",
        yref="paper",
        xanchor='left',
        yanchor='bottom',
        x=0,
        y=0,
        sizex=1,
        sizey=1,
        sizing="stretch",
        opacity=1,
        layer="below")],

    )
    fig = go.Figure(data=[trace1], layout=layout)
    file_path = 'maps_temp/cmx_finder-{}.png'.format(datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S"))
    local_path = os.path.join(app.static_folder, file_path)
    #print(saved_file_name)
    py.image.save_as(fig, local_path)

    relative_path = url_for('static', filename=file_path)
    return (local_path, relative_path)



