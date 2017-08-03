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
from __future__ import unicode_literals
from requests.auth import HTTPBasicAuth
#from apps import settings
import requests
import json
from APICaller import APICaller
import traceback
import cmxnotificationutil


class CMXAPICaller(APICaller): 
    
    API_V1 = "v1"
    API_V2 = "v2"
    API_LOCATION = "location"
    API_NOTIFICATION = "notification"
    API_MAPS = "maps"
    
    ZONES_SP = ["CENU>Torre Oeste>26andar>Cafe", "CENU>Torre Oeste>26andar>Demo Room"]
    API_ACCESS_SPL1 = ["CENU", "http://10.97.40.43:80/api", "rafacarv", "Cisco1234", API_V1, ZONES_SP] #admin/1234Qwer
    ZONES_DEVNET = ["DevNetCampus>DevNetBuilding>DevNetZone", "CiscoCampus>Building 9>IDEAS!"]
    API_ACCESS_SANDBOX = ["Devnet", "https://msesandbox.cisco.com:8081/api", "learning", "learning", API_V1, ZONES_DEVNET] #1
    
    
    ZONES_DCLOUD = []
    API_ACCESS_DCLOUD_INTERNAL = ["dCloud Demo - Internal", "http://web.cmx-drn-002.dc-01.com/api", "amdemo1", "C1sco12345", API_V2, ZONES_DCLOUD] #2
    API_ACCESS_DCLOUD_PARTNER = ["dCloud Demo - Partner", "https://web.cmx-drn-004.dc-01.com/api", "amdemo1", "C1sco12345", API_V2, ZONES_DCLOUD] #3
    
    API_REGISTERED_SERVERS = [API_ACCESS_SPL1, API_ACCESS_SANDBOX, API_ACCESS_DCLOUD_INTERNAL, API_ACCESS_DCLOUD_PARTNER]
    
    API_SERVER_NAME = ""
    API_BASE_URL = ""
    API_USERNAME = ""
    API_PASSWORD = ""
    API_VERSION = ""
    API_ZONES = ""
    API_ACCESS = None
          
    headers = ""

    def __init__(self, name, base_url, username, password, version="v1"):
        self.API_SERVER_NAME = name
        self.API_BASE_URL = base_url + "/api"
        self.API_USERNAME = username
        self.API_PASSWORD = password
        self.API_VERSION = version
        
        self.headers = {
            'content-type': "application/json"
        }
        super(CMXAPICaller, self).__init__("CMX",  auth_user=self.API_USERNAME, auth_pass=self.API_PASSWORD)    
            
            
    def __build_client_URL(self):
        return ("{}/location/{}/clients?sortBy=lastLocatedTime:DESC".format(self.API_BASE_URL, self.API_VERSION))
        
    def __build_zone_map_base_URL(self):
        return ("{}/config/{}/maps/image".format(self.API_BASE_URL, self.API_VERSION))
    
    def __build_image_source_map_base_URL(self):
        return ("{}/config/{}/maps/imagesource".format(self.API_BASE_URL, self.API_VERSION))
    
    def __build_notification_URL(self):
        return ("{}/config/{}/notification".format(self.API_BASE_URL, self.API_VERSION))
    
    def get_clients_list(self):
        url = self.__build_client_URL()
        return super(CMXAPICaller, self).requestHTTPJSON(url, "GET", self.headers)
    
    def get_client_information(self, macAddress, timeout=1):
        url = "{}/location/{}/clients/{}".format(self.API_BASE_URL, self.API_VERSION, macAddress)
        return super(CMXAPICaller, self).requestHTTPJSON(url, "GET", self.headers, timeout=timeout)
    
    def get_all_maps(self):
        url = "{}/config/{}/maps".format(self.API_BASE_URL, self.API_VERSION)
        return super(CMXAPICaller, self).requestHTTPJSON(url, "GET", self.headers)
    

    def subscribe_for_notification(self, notification_name, notification_type, notification_conditions, notification_uri, enable_MAC_scrambling=False):
        url = self.__build_notification_URL()
        payload = cmxnotificationutil.mount_notification_json(self.API_USERNAME, notification_name, notification_type, notification_conditions, notification_uri, enable_MAC_scrambling)
        #print (payload)
        return super(CMXAPICaller, self).requestHTTP(url, "PUT", self.headers, payload)
    
    
    def download_hierarchy_image (self, image_name):
        url = self.__build_image_source_map_base_URL() + "/" + image_name
        return self.download_file(url)
    
    def download_file(self, url):
        return super(CMXAPICaller, self).requestHTTP(url, "GET", self.headers, None)
    
    """  
    #Ignoring these functions for now.  
    def get_map_by_image_source(self, imageSourcePath):
        url = self.__build_image_source_map_base_URL()   
        url = url + "/" + imageSourcePath
        response = super(CMXAPICaller, self).requestHTTP(url, "GET")
        mapName = self.__save_image_file(response, imageSourcePath)
        return mapName
    
    
    def __save_image_file(self, httpResponse, name):
        filePath = "/files/" + name
        f = open(filePath,'wb')
        f.write(httpResponse.content)
        f.close()
        #CHANGE TO USE THIS http://bitsofpy.blogspot.com/2009/07/matplotlib-in-django.html
        #img = img[:, :, 0]
        #plt.savefig(f)
        return filePath
    """
    
    def subscribe_movement_notification(self, notification_uri, target_zone, mac_addresses, min_distance=50, device_type="client"):
        notification_type = "movement"
        conditions = []
        
        if (target_zone is not None):
            conditions.append("movement.hierarchy == {}".format(target_zone))
        
        mac_addresses = ';'.join(map(str,mac_addresses)) #adding ; separator
        conditions.append("movement.macAddressList == {}".format(mac_addresses))
        conditions.append("movement.distance > {}".format(min_distance))
        if (device_type != "all"):
            conditions.append("movement.deviceType == {}".format(device_type))
        
        notification_name = self.create_notification_name(self.API_SERVER_NAME, notification_type, device_type, target_zone)
        notification_name += "_{}".format(min_distance)
        
        self.subscribe_for_notification(notification_name, notification_type, conditions, notification_uri, enable_MAC_scrambling=False)
    
    def subscribe_location_update_notification(self, notification_uri, mac_addresses, target_zone=None, device_type="client"):
        conditions = []
        notification_type = "LocationUpdate"
        
        mac_addresses = ';'.join(map(str,mac_addresses)) #adding ; separator
        conditions.append("locationupdate.macAddressList == {}".format(mac_addresses))
        conditions.append("locationupdate.deviceType == {}".format(device_type))
        
        if (target_zone is not None):
            conditions.append("locationupdate.hierarchy == {}".format(target_zone))
        
        notification_name = self.create_notification_name(self.API_SERVER_NAME, notification_type, device_type, target_zone) 
        self.subscribe_for_notification(notification_name, notification_type, conditions, notification_uri, enable_MAC_scrambling=False)
    
    
    def subscribe_location_in_and_out (self, notification_uri, target_zone, mac_addresses, in_out="in", device_type="client"):
        conditions = []
        notification_type = "InOut"
        
        mac_addresses = ';'.join(map(str,mac_addresses)) #adding ; separator
        conditions.append("inout.macAddressList == {}".format(mac_addresses))
        conditions.append("inout.deviceType == {}".format(device_type))
        
        if (target_zone is not None):
            conditions.append("inout.hierarchy == {}".format(target_zone))
        
        conditions.append("inout.in/out == {}".format(in_out))
        
        notification_name = self.create_notification_name(self.API_SERVER_NAME, notification_type, device_type, target_zone)
        
        if (in_out == "in"):
            notification_name += "_ENTERING"
        else:
            notification_name += "_LEAVING"
            
        self.subscribe_for_notification(notification_name, notification_type, conditions, notification_uri, enable_MAC_scrambling=False)
    
    def create_notification_name(self, server_name, notification_type, device_type, target_zone=None):
        output = "{}_{}_{}".format(server_name, notification_type, device_type)
        
        if (target_zone is not None and target_zone != ""):
            output += "_{}".format(target_zone.replace(">", "-"))
        
        return output
    
    
    
    

if __name__ == "__main__":
    api = CMXAPICaller("devnet")
    
    
    server_info = api.get_all_maps()
    #print (json.dumps(server_info, indent=2))
    for campus in server_info["campuses"]:
        campus_name = campus["name"]
        campus_aesUid = campus["aesUid"]
        print ("{} ({})".format(campus_name, campus_aesUid))
        server_buildings = campus["buildingList"]
        
        
        #building = Building()
        
        if server_buildings is not None:
            for b in server_buildings:
                building_name = b["name"]
                print ("    {}".format(building_name))
                server_floors = b["floorList"]
                if server_floors is not None:
                    for f in server_floors:
                        
                        floor_name = f["name"]
                        floor_aesUid = f["aesUid"]
                        floor_calibrationModelId = f["calibrationModelId"]
                        
                        floor_length = f["dimension"]["length"]
                        floor_width = f["dimension"]["width"]
                        floor_height = f["dimension"]["height"]
                        floor_offsetX = f["dimension"]["offsetX"]
                        floor_offsetY = f["dimension"]["offsetY"]
                        floor_unit = f["dimension"]["unit"]
                        
                        image_name = f["image"]["imageName"]
                        image_zoom_level = f["image"]["zoomLevel"]
                        image_width = f["image"]["width"]
                        image_height = f["image"]["height"]
                        image_size = f["image"]["size"]
                        image_max_resolution = f["image"]["maxResolution"]
                        image_color_depth = f["image"]["colorDepth"]
                        
                        print ("        {}".format(floor_name))
                        server_zones = f["zones"] 
                        if (server_zones is not None):
                            for z in server_zones:
                                zone_name = z["name"]
                                zone_type = z["zoneType"]
                                print ("            {}".format(zone_name))
                        
    #map_name = json_obj["mapInfo"]["image"]["imageName"]
    #print (map_name)
    #print (api.get_map_by_image_source(map_name))
    
    #conditions = ["movement.distance > 50", "movement.hierarchy == DevNetCampus>DevNetBuilding>DevNetZone", "movement.macAddressList == 00:00:2a:01:00:1f;", "movement.deviceType == client"]
    #response = api.subscribe_for_notification("notification_name", "Movement", conditions, "https://cenu.herokuapp.com:80/cmx_webhook")
    #if (response.status_code == 201):
    #    print ("Notification created")
    #else:
    #    print ("Error occurred when trying to create the notification")
    