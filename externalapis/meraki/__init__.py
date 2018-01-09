import abc
from externalapis.APICaller import APICaller
import json

class IMerakiAPICaller (object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_client_information(self, mac_address):
        pass

    @abc.abstractmethod
    def get_clients_list(self, mac_address):
        pass


class MerakiHQDemoExtractor(IMerakiAPICaller, APICaller):
    API_BASE_URL = "http://live-map.meraki_old.com/clients"
    headers = ""

    def __init__(self):
        self.headers = {
            'content-type': "application/json"
        }
        super(MerakiHQDemoExtractor, self).__init__("MERAKI")

    def __build_client_URL(self, mac_address):
        return ("{}/{}".format(self.API_BASE_URL, mac_address))

    def get_client_information(self, mac_address):
        return super(MerakiHQDemoExtractor, self).requestHTTP(self.__build_client_URL(mac_address), "GET", self.headers)

    def get_clients_list(self, mac_address):
        return super(MerakiHQDemoExtractor, self).requestHTTP(self.__build_client_URL(mac_address), "GET", self.headers)
