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
import six
from datetime import datetime

class SparkCommandRequest (Base):
    __tablename__ = "spark_command_request"
    message_id = Column(String, primary_key=True, unique=True)
    command_category = Column(String, nullable=False)
    room_id = Column(String, nullable=False)
    person_id = Column(String, nullable=False)
    person_email = Column(String, nullable=False)
    created = Column(String, nullable=False)
    room_type = Column(String, nullable=False)
    message_text = Column(String, nullable=False)
    deployment_status = Column(String, nullable=False)

    def __init__(self, message_id, command_category, room_id, person_id, person_email, created, room_type, message_text, deployment_status):
        self.message_id = message_id
        self.command_category = command_category
        self.room_id = room_id
        self.person_id = person_id
        self.person_email = person_email
        self.room_type = room_type
        self.message_text = message_text
        self.deployment_status = deployment_status

        #
        if isinstance(created, six.string_types):
            #datetime_object = datetime.strptime(created, "%y-%M-%dTHH:mm:ss.SSS'Z'")
            #Format: yyyy-MM-dd'T'HH:mm:ss.SSSZ
            format = '%Y-%m-%dT%H:%M:%S.%fZ'
            datetime_object = datetime.strptime(created, format)

        else:
            datetime_object = created

        self.created = datetime_object
