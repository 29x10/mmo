from couchdb import ResourceNotFound
from pyramid.security import Allow, Everyone

class Container(object):

    def __init__(self, request, name="item", parent=None):
        self._request = request
        self.__name__ = name
        self.__parent__ = parent


    def __getitem__(self, id):
        db = self._request.db
        try:
            result = db[id]
        except ResourceNotFound:
            raise KeyError(id)

        result.__acl__ = [(Allow, Everyone, "view")]
        result.__name__ = id
        result.__parent__ = self
        return result

