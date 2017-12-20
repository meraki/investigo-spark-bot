from externalapis.APICaller import APICaller
from externalapis.meraki import IMerakiAPICaller


class MerakiHQDemoExtractor(IMerakiAPICaller, APICaller):
    API_BASE_URL = "http://live-map.meraki.com/clients"
    headers = ""

    def __init__(self):
        self.headers = {
            'content-type': "application/json"
        }
        super(MerakiHQDemoExtractor, self).__init__("MERAKI")

    def __build_client_url(self, mac_address):
        return "{}/".format(self.API_BASE_URL, mac_address)

    def get_clients(self):
        return super(MerakiHQDemoExtractor, self).requestHTTP(self.API_BASE_URL, "GET", self.headers)

    def get_client_information(self, mac_address):
        return super(MerakiHQDemoExtractor, self).requestHTTP(self.__build_client_url(mac_address), "GET", self.headers)
