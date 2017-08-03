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
from APICaller import APICaller
import traceback
import json
import urllib2
import requests, ConfigParser

class TropoAPICaller(APICaller):
    
    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open('api_config.ini'))
        api_key_voice = config.get('tropo', 'key_voice')
        api_key_text = config.get('tropo', 'key_text')
    except:
        print ("Working on Flask, so it will take configurations in another way")          

    tropoHeaders = {
            'Content-Type': 'application/json',
            'Accept': "application/json"
    }
    tropo_url = "https://api.tropo.com/1.0/sessions"
    
    def __init__(self, api_key_voice=None, api_key_text=None):
        if (api_key_voice is not None):
            self.api_key_voice = api_key_voice
        
        if (api_key_text is not None):
            self.api_key_text = api_key_text
              
        super(TropoAPICaller, self).__init__(APICaller.CISCO_APP_TROPO)
    
    def triggerTropo(self, type="voice", data=None):
        if (data is None):
            data = {}
        
        if (type != "voice"):
            data["token"] = self.api_key_text
        else:
            data["token"] = self.api_key_voice
        
        payload = json.dumps(data)
        return super(TropoAPICaller, self).requestHTTP(self.tropo_url, "POST", self.tropoHeaders, payload)    
    
    def triggerTropoWithMessageAndNumber(self, msg, number, voice="dave", type="voice"):
        params = {}
        params["msg"] = msg
        params["voice"] = voice
        
        if hasattr(number, 'lower'): #this means it is a string and not a list
            params["number"] = [number]
        else:
            params["number"] = number
        
        
        return self.triggerTropo(type, params)
       
if __name__ == '__main__':
    api = TropoAPICaller()
    
    city = "Las Vegas"
    #Builds the URL by adding the city name and the API's key
    url = "http://api.openweathermap.org/data/2.5/weather?mode=json&units=metric&q={}&APPID={}".format(urllib2.quote(city), "1f98bfe02a1e75fff95c88efdee5172b")
    
    #print (url)
    #Use that URL and request from the API server.
    api_response = requests.get(url)
    
    
    #Get the json-encoded content from response
    response_json = api_response.json()
    
    #print (json.dumps(response_json,indent=4))
    
    #Parsing the information to make sense out of it.
    temp = response_json["main"]["temp"]
    temp_min = response_json["main"]["temp_min"]
    temp_max = response_json["main"]["temp_max"]
    
    #Print an information that makes sense to the user.
    msg = "The temperature in {} is currently {} degrees Celsius. The maximum temperature today should be {}, while the lowest should not go below {}".format(city, temp, temp_max, temp_min)
    
    
    params = {}
    params["msg"] = msg
    print (msg)
    
    response = api.triggerTropoWithMessageAndNumber(msg, "tel:+1234567890", type="text")
    response = api.triggerTropoWithMessageAndNumber(msg, "sip:CEC@cisco.com;transport=tcp", type="voice")
    
    if (response.status_code == 200):
        print("Success")
    else:
        print ("Error triggering Tropo")