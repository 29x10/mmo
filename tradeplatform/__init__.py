from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import subscriber, BeforeRender
from pyramid.events import NewRequest
from couchdb.client import Server
from pyramid.security import Allow, Authenticated, authenticated_userid
from tradeplatform.modules.Container import Container
from tradeplatform.modules.tags import Tags
from tradeplatform.modules.zhanghao import Zhanghao

@subscriber(NewRequest)
def add_couchdb_tags_to_request(event):
    request = event.request
    settings = request.registry.settings
    db = settings['couchdb.server'][settings['couchdb.dbname']]
    event.request.db = db
    map_fun = Zhanghao.by_tag.map_fun
    reduce_fun = Zhanghao.by_tag.reduce_fun
    tag_row = db.query(map_fun=map_fun, reduce_fun=reduce_fun, group="true")
    tag_list = []
    for row in tag_row:
        tag_list.append(row.key)
    event.request.tag_list = tag_list

@subscriber(BeforeRender)
def context_processor(event):
    event.rendering_val['user_login'] = authenticated_userid(event['request'])
    event.rendering_val['tag_list'] = event['request'].tag_list

class RootFactory(object):
    def __init__(self, request):
        self._request = request
        self.__acl__ = [
            (Allow, Authenticated, 'view')
        ]

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    authn_policy = AuthTktAuthenticationPolicy(
        'sosecret', hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(settings=settings, root_factory=RootFactory)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    dbserver = Server(url = settings['couchdb.url'])
    if settings['couchdb.dbname'] not in dbserver:
        dbserver.create(settings['couchdb.dbname'])
    config.registry.settings['couchdb.server'] = dbserver
    config.add_renderer(".html", "pyramid.mako_templating.renderer_factory")
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('item', '/item/*traverse', factory=Container)
    config.add_route('tag', '/tag/*traverse', factory=Tags)
    config.scan()
    return config.make_wsgi_app()
