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

from flask import Blueprint, request, session, Response
from app.database import db_session
from app import get_meraki_validator_token, get_secret_key
#from app.mod_meraki_notification.models import CMXNotification

mod_meraki_notification = Blueprint('mod_meraki_notification', __name__, url_prefix='/meraki_old')

@mod_meraki_notification.route('/', methods=['GET', 'POST'])
def meraki():
    output = "No response"
    try:
        if request.method == "GET":
            try:
                validator = get_meraki_validator_token()
                output = validator
            except:
                # traceback.print_exc()
                output = 'Please add your validator to the environment variables. The name of the variable needs to be MERAKI_VALIDATOR'

        else:
            try:
                my_secret = get_secret_key()
            except:
                output = "WARNING: Your secret has not been set on the environment variables. The name of the variable needs to be MERAKI_SECRET"

            output = "Post Received. See logs for JSON"
            print (json.dumps(request.json))

    except:
        output = "Error when dealing with {}".format(request.method)
        traceback.print_exc()

    print (output)
    return (output)

"""
case 'POST':
            console.log("received CMX POST: " + event.body + " from Network "+network);
            var cmxJSON = JSON.parse(event.body);
            //console.log("cmxJSON object: " + JSON.stringify(cmxJSON, null, 2));
            if(cmxJSON.secret != secret){
                //console.log("secret invalid: "+ cmxJSON.secret);
                console.log("secret invalid from: "+ sourceIP);
                callback(null, {
                statusCode: '403',
                body: "INVALID SECRET",
                headers: {
                    'Content-Type': 'text/plain',
                }
            });
                return;
            }else{
                //console.log("secret accepted: "+ cmxJSON.secret);
                console.log("secret accepted from: "+ sourceIP);
            }

            // Check CMX JSON Version
            if (cmxJSON.version != '2.0'){
                // Prevent invalid version JSON from being sent. This is to avoid changes in schema which could result in data corruption.
                console.log("CMX Receiver is written for version 2.0 and will not accept other versions. The POST data was sent with version: "+ cmxJSON.version);
                return;
            }else{
                console.log("working with correct version: "+cmxJSON.version);
            }


            // Define paramaters for DynamoDB
            var params = {
                "TableName" : dynamoTable
                };
                params.Item = {};
            

            
            // Loop through the JSON object and add each observation to DynamoDB schema

            console.log('cmxJSON.data.apMac = '+cmxJSON.data.apMac);
            var key;
            var o = cmxJSON.data.observations;
            if(cmxJSON.type == "DevicesSeen"){
                console.log("type: DevicesSeen");
                for (key in o){
                    if (o.hasOwnProperty(key)) {
                        //console.log("Key is " + c + ", value is " + o[c].location.lat);
                        if (!o[key].location){break}
                        if (o[key].seenEpoch=== null || o[key].seenEpoch === 0){break}//  # This probe is useless, so ignore it
                        params.Item.type = cmxJSON.type;
                        params.Item.network = network;
                        params.Item.message_id = guid();
                        params.Item.message_ts = datetime.toString();
                        params.Item.name = o[key].clientMac;
                        params.Item.clientMac = o[key].clientMac;
                        params.Item.lat = o[key].location.lat;
                        params.Item.lng = o[key].location.lng;
                        params.Item.x = o[key].location.x[0];
                        params.Item.y = o[key].location.y[0];
                        params.Item.unc = o[key].location.unc;
                        params.Item.seenString = o[key].seenTime;
                        params.Item.seenEpoch = o[key].seenEpoch;
                        params.Item.apFloors = cmxJSON.data.apFloors || 0;
                        params.Item.manufacturer = o[key].manufacturer || "unknown";
                        params.Item.os = o[key].os || "unknown";
                        params.Item.ssid = o[key].ssid || "not connected";
                        params.Item.ipv4 = o[key].ipv4 || "unknown";
                        params.Item.ipv6 = o[key].ipv6 || "unknown";
                        params.Item.apMac = cmxJSON.data.apMac;
                        params.Item.apTags = cmxJSON.data.apTags.toString() || "none";
                    }
                    // Put Item in DynamoDB
                    dynamo.put(params, dynamoPutCallback);
                   
                }  // end for loop
            }else if(cmxJSON.type == "BluetoothDevicesSeen"){
                console.log("type: BluetoothDevicesSeen");
                for (key in o){
                    if (o.hasOwnProperty(key)) {
                        //console.log("Key is " + c + ", value is " + o[c].location.lat);
                        if (!o[key].location){break}
                        if (o[key].seenEpoch === null || o[key].seenEpoch === 0){break}//  # This probe is useless, so ignore it
                        params.Item.type = cmxJSON.type;
                        params.Item.message_id = guid();
                        params.Item.message_ts = datetime.toString();
                        params.Item.network = network;
                        params.Item.name = o[key].clientMac;
                        params.Item.clientMac = o[key].clientMac;
                        params.Item.lat = o[key].location.lat;
                        params.Item.lng = o[key].location.lng;
                        params.Item.x = o[key].location.x[0];
                        params.Item.y = o[key].location.y[0];
                        params.Item.unc = o[key].location.unc;
                        params.Item.seenString = o[key].seenTime;
                        params.Item.seenEpoch = o[key].seenEpoch;
                        params.Item.apFloors = cmxJSON.data.apFloors || 0;
                        params.Item.rssi = o[key].rssi;
                        params.Item.apMac = cmxJSON.data.apMac;
                        params.Item.apTags = cmxJSON.data.apTags.toString() || "none";
                    }

                    // Put Item in DynamoDB
                    dynamo.put(params, dynamoPutCallback);
                } // end for loop
            }else{
                console.log("unknown CMX 'type'");
                break;
            }

            // Respond to client with success
            callback(null, {
                statusCode: '200',
                body: "CMX POST RECEIVED",
                headers: {
                    'Content-Type': 'text/plain',
                }
            });
        break;


        default:
            // Respond to client with failure
            callback(null, {
                    statusCode: '403',
                    body: "request not recognized",
                    headers: {
                        'Content-Type': 'text/plain',
                    }
                });
        }

"""