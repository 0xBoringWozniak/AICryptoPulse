import time

from typing import Dict, List
from pymongo import ASCENDING, IndexModel

from service.mongo.database import ApplicationDatabaseException, DatabaseBase


class AppDatabase(DatabaseBase):

    NAME_DATABASE = 'application'

    # collection 'users'
    NAME_COLLECTION_USERS = 'users'
    NAME_FIELD_USERNAME = 'username'
    NAME_CHAT_ID = 'chat_id'
    NAME_FIELD_CREATION_DATE = 'creation_date'
    NAME_FIELD_SYSTEM_PROMPT = 'system_prompt'

    SCHEMA_USERS = \
        {
            '$jsonSchema':
                {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': [NAME_FIELD_CREATION_DATE, NAME_FIELD_SYSTEM_PROMPT],
                    'properties':
                        {
                            NAME_FIELD_CREATION_DATE: {
                                    'bsonType': 'double'
                                },
                            NAME_FIELD_SYSTEM_PROMPT: {
                                    'bsonType': 'string'
                                },
                            NAME_FIELD_USERNAME: {
                                    'bsonType': 'string'
                                },
                            NAME_CHAT_ID: {
                                    'bsonType': 'string'
                                }
                        }
                }
        }

    INDEXES_USERS = [IndexModel([(NAME_FIELD_USERNAME, ASCENDING)],
                                name='INDEX_USERNAME', background=True, unique=True)]

    def __init__(self, db_host: str, db_port: int,
                 db_user: str = None, db_user_password: str = None,
                 encryption_cmk: bytes = None):

        super().__init__(db_host=db_host, db_port=db_port, db_name=self.NAME_DATABASE,
                         db_user=db_user, db_user_password=db_user_password,
                         encryption_cmk=encryption_cmk)

        self.connected = False

        if encryption_cmk is not None and self.client_encryption is None:
            raise ApplicationDatabaseException('Encryption must be set up but it\'s not.')

        self.collections_schemas = {
            self.NAME_COLLECTION_USERS: self.SCHEMA_USERS,
        }

        self.collections_indexes = {
            self.NAME_COLLECTION_USERS: self.INDEXES_USERS,
        }

        self._create_collections()

        self.collection_users = self.database[self.NAME_COLLECTION_USERS]

        self.connected = True

    def has_user(self, username: str) -> bool:
        self._verify_type(username, str)
        try:
            found_user_id = self.collection_users.find_one(
                {self.NAME_FIELD_USERNAME: username},)
        except Exception as e:
            raise ApplicationDatabaseException(str(e)) from e
        return found_user_id is not None

    def add_user(self, username: str, system_prompt: str, chat_id: str) -> None:
        self._verify_type(username, str)
        self._verify_type(system_prompt, str)
        try:
            found_user_id = self.collection_users.find_one(
                {self.NAME_FIELD_USERNAME: username},)
            if found_user_id is not None:
                raise ApplicationDatabaseException(
                    f'User with {username} already exists in the system.'
                )

            now = time.time()

            self.collection_users.insert_one({
                self.NAME_FIELD_CREATION_DATE: now,
                self.NAME_FIELD_SYSTEM_PROMPT: system_prompt,
                self.NAME_FIELD_USERNAME: username,
                self.NAME_CHAT_ID: chat_id,
            })

        except Exception as e:
            raise ApplicationDatabaseException(str(e)) from e

    def remove_user(self, username: str) -> None:
        self._verify_type(username, str)
        try:
            self.collection_users.delete_one({
                self.NAME_FIELD_USERNAME: username,
            })
        except Exception as e:
            raise ApplicationDatabaseException(str(e)) from e

    def set_user_prompt(self, username: str, new_prompt: str) -> None:
        self._verify_type(username, str)
        self._verify_type(new_prompt, str)
        try:
            self.collection_users.update_one(
                {self.NAME_FIELD_USERNAME: username},
                {'$set': {self.NAME_FIELD_SYSTEM_PROMPT: new_prompt}},
            )
        except Exception as e:
            raise ApplicationDatabaseException(str(e)) from e

    def get_user_info(self, username: str) -> Dict:
        self._verify_type(username, str)
        if not self.has_user(username):
            raise ApplicationDatabaseException(f'User {username} not found.')
        try:
            user_info = self.collection_users.find_one(
                {self.NAME_FIELD_USERNAME: username})
        except Exception as e:
            raise ApplicationDatabaseException(str(e)) from e
        return user_info

    def get_all_users(self) -> List[Dict]:
        try:
            users = self.collection_users.find({})
        except Exception as e:
            raise ApplicationDatabaseException(str(e)) from e
        return [user for user in users]
