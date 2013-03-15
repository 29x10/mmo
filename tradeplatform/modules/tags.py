from couchdb import ResourceNotFound
from pyramid.security import Allow, Everyone
from tradeplatform.modules.zhanghao import Zhanghao


class Tags(object):

    def __init__(self, request, name="tag", parent=None):
        self._request = request
        self.__name__ = name
        self.__parent__ = parent


    def __getitem__(self, tag):
        db = self._request.db
        map_fun = Zhanghao.each_tag.map_fun
        result = db.query(map_fun, startkey=[tag, {}], endkey=[tag], descending=True)

        result.__acl__ = [(Allow, Everyone, "view")]
        result.__name__ = tag
        result.__parent__ = self
        return result

