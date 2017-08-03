'''
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
'''
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
import xmltodict
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class APICaller(object):

    CISCO_APP_ISE = "ISE"
    CISCO_APP_SPARK = "SPARK"
    CISCO_APP_CMX = "CMX"
    CISCO_APP_TROPO = "TROPO"

    cisco_app_name = "None set"
    #used for CMX Basic Authentication
    auth_user = None
    auth_pass = None
    

    def __init__(self, cisco_app_name, auth_user=None, auth_pass=None):
        self.cisco_app_name = cisco_app_name
        self.auth_user = auth_user
        self.auth_pass = auth_pass
        
    def requestHTTP(self, url, method, headers=None, payload=None, verify=True, timeout=None):
        self.log (url)
        
        if self.auth_user and self.auth_pass:
            response = requests.request(method, url, auth=HTTPBasicAuth(self.auth_user, self.auth_pass), data=payload, headers=headers, verify=verify, timeout=timeout)
        else: 
            response = requests.request(method, url, data=payload, headers=headers,  timeout=timeout)

        if response.status_code == 200:
            self.log ("Success")
        elif response.status_code == 201:
            self.log ("Created")
        elif response.status_code == 204:
            self.log ("No content")
        elif response.status_code == 302:
            raise Exception("Incorrect credentials provided")
        elif response.status_code == 400:
            if(self.cisco_app_name != self.CISCO_APP_ISE):
                response_content = response.content
                #response_json = response.json()
                raise Exception("Invalid request: %s" % response_content)
            else:
                raise Exception(response.content)
        
        elif response.status_code == 401:
            raise Exception("Unauthorized access")
        elif response.status_code == 403:
            raise Exception("Forbidden access to the REST API")
        elif response.status_code == 404:
            raise Exception("URL not found %s" % response.url)
        elif response.status_code == 406:
            raise Exception("The Accept header sent in the request does not match a supported type")
        elif response.status_code == 415:
            raise Exception("The Content-Type header sent in the request does not match a supported type")
        elif response.status_code == 500:
            if(self.cisco_app_name != self.CISCO_APP_ISE):
                print (response.content)
                raise Exception("An error has occurred during the API invocation")
            else:
                #ISE has a different behavior, as the HTTP 500 can actually mean something
                pass   
        elif response.status_code == 502:
            raise Exception("The server is down or being upgraded")
        elif response.status_code == 503:
            raise Exception("The servers are up, but overloaded with requests. Try again later (rate limiting)")
        else:
            raise APIError("Unknown Request Error, return code is %s" % response.status_code)
        
        #if (response.status_code == 200):
        #    self.logWithCiscoAppName ("Success!")
        #else:
        #    self.logWithCiscoAppName (("Status: {} - Body {}").format(response.status_code, response.content))
        
        return response
    
    def requestHTTPJSON(self, url, method, headers=None, payload=None, verify=True, timeout=None):
        httpResponse = self.requestHTTP(url, method, headers, payload, verify, timeout=timeout)
        if httpResponse.status_code == 204:
            # 204 means No content
            response_json = {}
        else:
            response_json = httpResponse.json() # Get the json-encoded content from response with "response_json = resp.json()
        #self.logWithCiscoAppName (json.dumps(response_json,indent=2))
        return response_json
    
    def requestHTTPXMLTOJSON(self, url, method, headers=None, payload=None, verify=True):
        #print (payload)
        httpResponse = self.requestHTTP(url, method, headers, payload, verify)
        response_json = xmltodict.parse(httpResponse.content)
        return response_json
    
    
    
    def __requestHTTPGET(self,request, url):
        return request.get(url)
    
    def __requestHTTPPOST(self, request, url):
        return request.post(url)
    
    def log (self, message):
        now = datetime.now().strftime("%Y/%m/%dT%H:%M:%S")
        formatted = "[{}][{}] {}".format(now, self.cisco_app_name, message)
        print (formatted)
        
    @staticmethod
    def FORMAT_REQUEST_FIELDS (url, method, headers=None, payload=None, verify=False):
        output = {}
    
        output["url"] = url
        output["method"] = method
        output["headers"] = headers
        output["payload"] = payload
        output["verify"] = verify
    
        return output
    
class APIError(Exception):
    """
    Generic error raised by the API module.
    """