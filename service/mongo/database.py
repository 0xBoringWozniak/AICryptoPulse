import logging
from abc import ABC
from typing import Any, Dict, Type, Union

from pymongo import IndexModel, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.encryption import ClientEncryption
from pymongo.encryption_options import AutoEncryptionOpts
from pymongo.errors import CollectionInvalid


class ApplicationDatabaseException(Exception):

    def __init__(self, message: str):
        self.message: str = message

    def __str__(self) -> str:
        return self.message


class ApplicationDatabaseNotFoundException(ApplicationDatabaseException):
    pass


class DatabaseParameters():

    def __init__(self, db_host: Union[str, None], db_port: Union[int, None],
                 db_user: str = None, db_user_password: Union[str, None] = None,
                 encryption_cmk: Union[bytes, None] = None):
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_user_password = db_user_password
        self.encryption_cmk = encryption_cmk


class DatabaseBase(ABC):

    def __init__(self, db_host: str, db_port: int, db_name: str,
                 db_user: str = None, db_user_password: str = None,
                 encryption_cmk: bytes = None
                 ):
        self.database: Union[Database, None] = None
        self.collections_schemas: Dict[str, Any] = {}
        self.collections_indexes: Dict[str, Any] = {}
        self.connected: bool = False

        if db_host is not None:
            print(db_host)
            self._verify_type(db_host, str)
        if db_port is not None:
            self._verify_type(db_port, int)
        self._verify_type(db_name, str)
        if db_user is not None:
            self._verify_type(db_user, str)
        if db_user_password is not None:
            self._verify_type(db_user_password, str)
        if encryption_cmk is not None:
            self._verify_type(encryption_cmk, bytes)
            if len(encryption_cmk) != 96:
                logging.error('Wrong length of the encryption CMK - must be 96.')
                raise ApplicationDatabaseException('Wrong length of the encryption CMK - must be 96.')

        self.encryption_db_name = 'encryption'
        self.encryption_coll_name = 'key_vault'
        self.auth_source = 'admin'

        mongo_client_kwargs: Dict[str, Any] = {}

        if db_user is not None and db_user_password is not None:
            mongo_client_kwargs['authSource'] = self.auth_source
            mongo_client_kwargs['username'] = db_user
            mongo_client_kwargs['password'] = db_user_password

        if encryption_cmk is not None:
            self.kms_providers = {"local": {"key": encryption_cmk}}
            self.key_vault_namespace = f'{self.encryption_db_name}.{self.encryption_coll_name}'
            self.auto_encryption_opts = AutoEncryptionOpts(
                self.kms_providers, self.key_vault_namespace, bypass_auto_encryption=True)
            mongo_client_kwargs['auto_encryption_opts'] = self.auto_encryption_opts

        try:
            self.db_client: MongoClient = MongoClient(host=db_host, port=db_port, **mongo_client_kwargs)
            self.db_client.admin.command('ping')
            self.database = self.db_client[db_name]

            if encryption_cmk is not None:
                self.client_encryption: ClientEncryption =\
                    ClientEncryption(self.kms_providers, self.key_vault_namespace,
                                     self.db_client, self.db_client.codec_options)

        except Exception as e:
            error_message = f'Can not connect to {db_host}:{db_port}/{db_name}:\'{e}\''
            logging.info(error_message)
            raise ApplicationDatabaseException(error_message) from e

        self.connected = True

    def _create_collections(self) -> None:
        for key in self.collections_schemas:
            self._create_collection_if_required(collection_name=key)

    def _create_collection_if_required(self, collection_name: str):

        assert isinstance(collection_name, str)

        try:
            if collection_name in self.collections_schemas:
                self.database.create_collection(collection_name,
                                                validator=self.collections_schemas[collection_name])
            else:
                raise ApplicationDatabaseException(f'Unexpected collection name whilst creation:\'{collection_name}\'.')

            # create alias for collection inside the current database object for easier programming
            self.__dict__[f'collection_{collection_name}'] = self.database[collection_name]

            # create indexes for faster search inside the collections
            # only in case the collection has been just created
            if collection_name in self.collections_indexes:
                collection_indexes = self.collections_indexes[collection_name]
                assert isinstance(collection_indexes, list)
                if len(collection_indexes) == 0:
                    return
                for index in collection_indexes:
                    assert isinstance(index, IndexModel)
                self.database[collection_name].create_indexes(collection_indexes)

        except CollectionInvalid as e:
            logging.info('Collection %s has been created earlier: %s.', collection_name, str(e))
            return
        except Exception as e:
            logging.error('Unexpected exception whilst creation the collection %s:%s.', collection_name, str(e))
            raise ApplicationDatabaseException('Unexpected exception whilst creation the collection %s:%s.') from e

    @staticmethod
    def _verify_type(variable: Any, type_of_variable: Type):
        if not isinstance(variable, type_of_variable):
            raise ApplicationDatabaseException(
                f'Variable {variable} type mismatch: got {type(variable)} instead of {type_of_variable}')

    def _clear_collection(self, collection: Collection) -> None:
        try:
            collection_name = collection.name
            collection.drop()
            self._create_collection_if_required(collection_name=collection_name)

        except Exception as e:
            logging.error(str(e))
            raise ApplicationDatabaseException(str(e)) from e

    @staticmethod
    def _get_collection_records_number(collection: Collection) -> int:
        try:
            return collection.count_documents({})
        except Exception as e:
            logging.error(str(e))
            raise ApplicationDatabaseException(str(e)) from e
