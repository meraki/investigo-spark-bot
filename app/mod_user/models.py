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
from app.database import Base


class RegisteredUser(Base):
    __tablename__ = "registered_user"
    id = Column(Integer, primary_key=True, unique=True)
    mac_address = Column(String, unique=True)
    name = Column(String)
    phone = Column(String)

    def __init__(self, name, mac_address, phone=None):
        self.name = name
        self.mac_address = mac_address
        self.phone = phone

    def __repr__(self):
        return "{} ({})".format(self.name, self.mac_address)

    def serialize(self):
        out = {
            "name": self.name,
            "phone": self.phone,
            "mac_address": self.mac_address,
            "id": self.id
        }
        return out
