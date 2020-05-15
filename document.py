import builtins
import pickle
from datetime import datetime
import inspect
import pymongo


"""
Abstract model for all mongodb document models
"""

database = None


class Document(object):

    # represents the collection in which the subclasses will be stored
    _collection = None

    # specifies the id document field
    _id_field = "_id"

    # attributes to ignore during parsing
    _parse_ignore = []

    # attributes which are open for public
    _marshaled: list = ()

    # mandatory fields. If this fields are None, an exception is thrown
    _mandatory_fields: list = ()

    # values which will be saved as ref only and are loaded when needed
    # TODO

    def __init__(self, _db=None, **kwargs):

        # set database
        if _db:
            global database
            database = _db

        self.decode(kwargs)

        if self._mandatory_fields is not None and len(self._mandatory_fields) > 0:
            for field in self._mandatory_fields:
                v = getattr(self, field, None)
                if v is None:
                    raise IOError(f"Field {field} must be set!")

        # check collection
        if self._collection not in Document._get_db().collection_names(include_system_collections=False):
            Document._get_db().create_collection(self._collection)
            Document._get_db().get_collection(self._collection).create_index([(self._id_field, pymongo.ASCENDING)],
                                                                             unique=True)

    def decode(self, data: dict):

        for key, val in [(key, val) for key, val in data.items()
                         if key in self.__dir__() and not key.startswith("_")]:

            if isinstance(val, dict) and "_type" in val:
                if val["_type"] == "binary":
                    self.__dict__.update({key: pickle.loads(val["_data"])})

                else: # val type == Document

                    # reference TODO
                    if "_id" in val and "_id_val" in val:
                        # load data of db
                        self.__dict__.update({key: val["_type"].get(**{val["_id"]: val["_id_val"]})})
                    else:
                        self.__dict__.update({key: val["_type"](**val["_data"])})
            else:
                self.__dict__.update({key: val})

    @staticmethod
    def _get_db(db=None):
        if not db and not database:
            raise IOError("No db set")
        else:
            return db or database

    # parses the current subclass instance and stores it into the subclass collection
    def save(self):
        try:
            Document._get_db()[self.__class__._collection].insert_one(self.__class__.serialize(self, self._parse_ignore))
        except Exception as e:
            raise IOError("Could not insert document")
        return self

    # parse python object into dict. Ignore all __foo__ keys
    def serialize(self, datetime_to_int=False, ignor=()):
        result = dict()

        for key, val in [(key, getattr(self, key)) for key in dir(self) if not key.startswith("_")]:

            if key in result.keys() or inspect.ismethod(val) or val is None:
                continue
            if type(val) in [int, float, str, bool, datetime, tuple, dict, list]:
                if datetime_to_int and isinstance(val, datetime):
                    result[key] = val.timestamp()
                else:
                    result[key] = val
            elif isinstance(val, Document):
                result.update({key: {"_type": "document", "_data": val.serialize(ignor)}})
            else:
                result.update({key: {"_type": "binary", "_data": pickle.dumps(val)}})

        return result

    # updates keyword items in db and object
    def update_data(self, **kwargs):
        Document._get_db()[self.__class__._collection].update_one(
            {self._id_field: self.__dict__[self._id_field]},
            {"$set": {key: value for key, value in kwargs.items() if key != self._id_field}})
        self.__dict__.update(kwargs)

    def update(self):
        Document._get_db()[self.__class__._collection].update_one(
            {self._id_field: self.__dict__[self._id_field]},
            {"$set": {key: value for key, value in vars(self).items() if key != self._id_field}})

    def delete(self):
        Document._get_db()[self.__class__._collection].delete_one({self._id_field: self.__dict__[self._id_field]})

    # request document by key=value. Bsp: user_id="testuser"
    @classmethod
    def get(cls, **kwargs):

        data = Document._get_db()[cls._collection].find_one({key: value for key, value in kwargs.items()})
        if data is not None:
            return cls(**data)

    @classmethod
    def aggregate(cls, pipeline):

        data = Document._get_db()[cls._collection].aggregate(pipeline)
        if data is not None:
            return [cls(**dat) for dat in data]

    @classmethod
    def get_all(cls, **kwargs):

        data = Document._get_db()[cls._collection].find({key: value for key, value in kwargs.items() if key != "limit"}) \
            .limit(kwargs.get("limit", 200))
        if data is not None:
            return [cls(**dat) for dat in data]

    @classmethod
    def count(cls, **kwargs):

        return Document._get_db()[cls._collection].find({key: value for key, value in kwargs.items()}).count()

    # Returns all values as dict
    def dump(self, marshaled=False):
        return {k: v for k,v in self.serialize(datetime_to_int=True, ignor=self._parse_ignore).items()
                if not marshaled or k in self._marshaled}

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return hash(str(self.serialize())) == hash(str(other.serialize()))




