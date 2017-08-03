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
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Numeric, DateTime, BigInteger

from app.database import Base


class CMXNotification(Base):
    __tablename__ = 'cmx_notification'
    mac_address = Column(String, primary_key=True, unique=True)  # deviceId
    notification_type = Column(String, nullable=False)
    subscription_name = Column(String, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    last_seen = Column(String, nullable=False)
    event_id = Column(Integer)
    floor_id = Column(BigInteger)
    band = Column(String)
    entity = Column(String)
    location_map_hierarchy = Column(String)
    location_x = Column(Numeric)  # locationCoordinate.x
    location_y = Column(Numeric)  # locationCoordinate.y
    location_z = Column(Numeric)  # locationCoordinate.z
    location_unit = Column(String, default="FEET")
    ssid = Column(String)
    ap_mac_address = Column(String)
    confidence_factor = Column(Integer)
    absence_duration_minutes = Column(Integer)

    def __init__(self, mac_address, notification_type, subscription_name, timestamp, confidence_factor, last_seen, event_id, floor_id, band, entity, location_map_hierarchy, location_x, location_y, location_z, location_unit, ssid, ap_mac_address, absence_duration_minutes):
        self.mac_address = mac_address
        self.notification_type = notification_type
        self.subscription_name = subscription_name
        self.timestamp = timestamp
        self.confidence_factor = confidence_factor
        self.last_seen = last_seen
        self.event_id = event_id
        self.floorId = floor_id
        self.band = band
        self.entity = entity
        self.ssid = ssid
        self.location_map_hierarchy = location_map_hierarchy
        self.location_x = location_x
        self.location_y = location_y
        self.location_z = location_z
        self.location_unit = location_unit
        self.ap_mac_address = ap_mac_address
        self.absence_duration_minutes = absence_duration_minutes
