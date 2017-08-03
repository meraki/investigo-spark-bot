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
from APICaller import APICaller

class SparkAPICaller(APICaller):
    API_SPARK_PRODUCTION = ["Spark", "https://api.ciscospark.com", "Bearer", "OWQzZGE4YTItNDZkMC00MTVkLTk4NzMtNzBkY2RmNDI4MDllZThkYTIyNzItMzI5"]
    API_REGISTERED_SERVERS = [API_SPARK_PRODUCTION]
    API_ACCESS = API_REGISTERED_SERVERS[0]
    
    API_V1 = "v1"
    
    API_MESSAGES = "messages"
    API_ROOMS = "rooms"
    API_WEBHOOKS = "webhooks"
    API_PEOPLE = "people"
    
    API_BASE_URL = API_ACCESS[1]
    API_AUTHENTICATION_TYPE = API_ACCESS[2]
    API_AUTHENTICATION_ID = API_ACCESS[3]
    
    VERSION = API_V1
    
    sparkHeaders = ""
    
    def __init__(self, token=None):
        super(SparkAPICaller, self).__init__("SPARK")

        if token:
            self.API_AUTHENTICATION_ID = token

        self.sparkHeaders = {
            'authorization': "{} {}".format(self.API_AUTHENTICATION_TYPE, self.API_AUTHENTICATION_ID),
            'content-type': "application/json",
            'cache-control': "no-cache",
        }
    
    def postMessage(self, roomId, text, toPersonId=None, toPersonEmail=None, markdown=None, files=None):
        #https://developer.ciscospark.com/endpoint-messages-post.html 
        data = {}
        if (roomId):
            data["roomId"] = roomId
        if (toPersonId):
            data["toPersonId"] = toPersonId
        if (toPersonEmail):
            data["toPersonEmail"] = toPersonEmail
        if (text):
            if (len (text) > 7439):
                text = text[:7439]
            data["text"] = text
        if (markdown):
            if (len (markdown) > 7439):
                markdown = markdown[:7439]
            data["markdown"] = markdown
        if (files):
            data["files"] = files


        print(json.dumps(data, indent=2))

        payload = json.dumps(data)



        
        url = self.__buildURLMessages() 
        return super(SparkAPICaller, self).requestHTTP(url, "POST", self.sparkHeaders, payload)
    
    
    

    def createWebhookSimplified(self, webhook_name, webhook_targetUrl, webhook_resource, webhook_roomId):
        
        webhook_event = "created"
        webhook_filter = "roomId={}".format(webhook_roomId)
        self.createWebhook(webhook_name, webhook_targetUrl, webhook_resource, webhook_event, webhook_filter, None)
    
    def createWebhook (self, webhook_name, webhook_targetUrl, webhook_resource, webhook_event, webhook_filter, webhook_secret):
        #https://developer.ciscospark.com/endpoint-webhooks-post.html 
        
        if (webhook_name and webhook_targetUrl and webhook_resource and webhook_event):
            data = {}
            data["name"] = webhook_name
            data["targetUrl"] = webhook_targetUrl
            data["resource"] = webhook_resource
            data["event"] = webhook_event
            if (webhook_filter):
                data["filter"] = webhook_filter
            if (webhook_secret):
                data["secret"] = webhook_secret
            payload = json.dumps(data)
                
            url = self.__buildURLWebhook() 
            return super(SparkAPICaller, self).requestHTTP(url, "POST", self.sparkHeaders, payload)
        else:
            super(SparkAPICaller, self).log ("Required arguments not passed.")
    
    def getPersonDetails(self, webhook_personId):
        if (webhook_personId):
            url = self.__buildURLPeople() + "/" + webhook_personId
            return super(SparkAPICaller, self).requestHTTPJSON(url, "GET", self.sparkHeaders, None)
        else:
            print ("Required argument not passed.")
    
    def getMessage(self, messageId):
        url = self.__buildURLMessages() + "/" + messageId
        json = super(SparkAPICaller, self).requestHTTPJSON(url, "GET", self.sparkHeaders, None)
        return json["text"]
        
    def getRooms(self):    
        url = self.__buildURLRooms()
        server_response = super(SparkAPICaller, self).requestHTTPJSON(url, "GET", self.sparkHeaders, None)
        #returnText = json.dumps(server_response)
        #Returing JSON itself
        return server_response
    
    #HELPER METHODS TO CREATE URL's
    def __buildURLMessages(self):
        return "{}/{}/{}".format(self.API_BASE_URL, self.API_V1, self.API_MESSAGES)
    
    def __buildURLRooms(self):
        return "{}/{}/{}".format(self.API_BASE_URL, self.API_V1, self.API_ROOMS)
    
    def __buildURLWebhook(self):
        return "{}/{}/{}".format(self.API_BASE_URL, self.API_V1, self.API_WEBHOOKS)
    
    def __buildURLPeople(self):
        return "{}/{}/{}".format(self.API_BASE_URL, self.API_V1, self.API_PEOPLE)
    
if __name__ == "__main__":
    pass
    sparkApi = SparkAPICaller()
    #sparkApi.log(sparkApi.getMessage("Y2lzY29zcGFyazovL3VzL01FU1NBR0UvNmE4NjI0MjAtNDlkMC0xMWU2LWIwZjMtYTNlMzhkMzIyZGY1"))
    sparkApi.postMessage("Y2lzY29zcGFyazovL3VzL1JPT00vYTY0NDFmMDAtNWZmNC0xMWU2LTkwODctN2IzY2QxMWYwYzg3", None, None, "Testing spark", None, None)   