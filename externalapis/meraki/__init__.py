import abc
from externalapis.APICaller import APICaller
import json
import gzip

class IMerakiAPICaller (object):
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    def get_client_information(self, mac_address):
        pass

    @abc.abstractmethod
    def get_clients_list(self, mac_address):
        pass

    # Adding modularity to accomodate Meraki deployment.
    deployment_type = "Cloud"
    demo = False


class MerakiHQDemoExtractor(IMerakiAPICaller, APICaller):
    API_BASE_URL = "http://live-map.meraki.com/clients"
    headers = ""
    demo = True

    def __init__(self):
        self.headers = {
            'content-type': "application/json"
        }
        super(MerakiHQDemoExtractor, self).__init__("MERAKI")

    def __build_client_url(self, mac_address):
        return "{}/{}".format(self.API_BASE_URL, mac_address)

    def get_clients_list(self):
        return super(MerakiHQDemoExtractor, self).requestHTTPJSON(self.API_BASE_URL, "GET", self.headers)

    def get_client_information(self, mac_address):
        server_output = super(MerakiHQDemoExtractor, self).requestHTTPJSON(self.__build_client_url(mac_address), "GET",
                                                                           self.headers)
        return server_output
