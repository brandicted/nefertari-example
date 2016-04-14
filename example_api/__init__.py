from pkg_resources import get_distribution
import logging

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
import cryptacular.bcrypt

import nefertari
from nefertari.tweens import enable_selfalias
from nefertari.utils import dictset
from nefertari.acl import RootACL as NefertariRootACL

APP_NAME = __package__.split('.')[0]
_DIST = get_distribution(APP_NAME)
PROJECTDIR = _DIST.location
__version__ = _DIST.version

log = logging.getLogger(__name__)

Settings = dictset()


def bootstrap(config):
    Settings.update(config.registry.settings)
    Settings[APP_NAME + '.__version__'] = __version__
    Settings[nefertari.APP_NAME+'.__version__'] = nefertari.__version__

    config.include('nefertari')

    root = config.get_root_resource()
    root.default_factory = 'nefertari.acl.RootACL'

    config.include('example_api.models')
    config.include('nefertari.view')
    config.include('nefertari.elasticsearch')
    config.include('nefertari.json_httpexceptions')

    enable_selfalias(config, 'user_username')

    if Settings.asbool('enable_get_tunneling'):
        config.add_tween('nefertari.tweens.get_tunneling')

    if Settings.asbool('cors.enable'):
        config.add_tween('nefertari.tweens.cors')

    if Settings.asbool('ssl_middleware.enable'):
        config.add_tween('nefertari.tweens.ssl')

    if Settings.asbool('request_timing.enable'):
        config.add_tween('nefertari.tweens.request_timing')

    if Settings.asbool('auth', False):
        config.add_request_method(
            'example_api.models.User.get_authuser_by_userid',
            'user', reify=True)
    else:
        log.warning('*** USER AUTHENTICATION IS DISABLED ! ***')

    def _route_url(request, route_name, *args, **kw):
        if config.route_prefix:
            route_name = '%s_%s' % (config.route_prefix, route_name)
        return request.route_url(route_name, *args, **kw)

    config.add_request_method(_route_url)

    def _route_path(request, route_name, *args, **kw):
        if config.route_prefix:
            route_name = '%s_%s' % (config.route_prefix, route_name)
        return request.route_path(route_name, *args, **kw)

    config.add_request_method(_route_path)


def main(global_config, **settings):
    Settings.update(settings)
    Settings.update(global_config)
    authz_policy = ACLAuthorizationPolicy()
    config = Configurator(
        settings=settings,
        authorization_policy=authz_policy,
        root_factory=NefertariRootACL,
    )

    config.include('nefertari.engine')

    from example_api.models import Profile
    from example_api.models import User
    authn_policy = AuthTktAuthenticationPolicy(
        Settings['auth_tkt_secret'],
        callback=User.get_groups_by_userid,
        hashalg='sha512',
        cookie_name='example_api_auth_tkt',
        http_only=True,
    )
    config.set_authentication_policy(authn_policy)

    config.include(includeme)

    from nefertari.engine import setup_database
    setup_database(config)

    from nefertari.elasticsearch import ES
    ES.setup_mappings()

    setup_event_handlers(config)

    config.commit()
    initialize()

    return config.make_wsgi_app()


def setup_event_handlers(config):
    config.include('nefertari.authentication')

    from nefertari import events
    from example_api.models import User

    def hide_user_passwords(event):
        if event.view._auth_enabled:
            event.set_field_value('password', 'VERY_SECRET')

    config.subscribe_to_events(
        hide_user_passwords,
        [events.AfterIndex, events.AfterShow],
        model=User,
    )


def includeme(config):
    log.info("%s %s" % (APP_NAME, __version__))

    bootstrap(config)

    config.scan(package='example_api.views')

    root = config.get_root_resource()
    root.add('account',
             view='example_api.views.account.TicketAuthRegisterView',
             factory='nefertari.acl.AuthenticationACL')
    root.add('login',
             view='example_api.views.account.TicketAuthLoginView',
             factory='nefertari.acl.AuthenticationACL')
    root.add('logout',
             view='example_api.views.account.TicketAuthLogoutView',
             factory='nefertari.acl.AuthenticationACL')

    create_resources(config)


def create_resources(config):
    root = config.get_root_resource()

    user = root.add(
        'user', 'users',
        id_name='user_username',
        factory="example_api.acl.UsersACL")

    user.add('group', 'groups',
             view='example_api.views.users.UserAttributesView',
             factory="example_api.acl.UsersACL")
    user.add('setting', 'settings',
             view='example_api.views.users.UserAttributesView',
             factory="example_api.acl.UsersACL")
    user.add('profile',
             view='example_api.views.users.UserProfileView',
             factory="example_api.acl.UsersACL")

    root.add(
        'story', 'stories',
        id_name='story_id',
        factory="example_api.acl.StoriesACL")


def initialize():
    from example_api.models import User
    import transaction
    crypt = cryptacular.bcrypt.BCRYPTPasswordManager()
    log.info('Initializing')
    try:
        s_user = Settings['system.user']
        s_pass = str(crypt.encode(Settings['system.password']))
        s_email = Settings['system.email']
        log.info('Creating system user')
        user, created = User.get_or_create(
            username=s_user,
            defaults=dict(
                password=s_pass,
                email=s_email,
                groups=['admin'],
            ))
        changed = created
        if not created and Settings.asbool('system.reset'):
            log.info('Resetting system user')
            user.password = s_pass
            user.email = s_email
            user.save()
            changed = True
        if changed:
            transaction.commit()

    except KeyError as e:
        log.error('Failed to create system user. Missing config: %s' % e)
