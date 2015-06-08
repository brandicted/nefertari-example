from pkg_resources import get_distribution
import logging

from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator

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
    root.auth = Settings.asbool('auth')
    root.default_factory = 'nefertari.acl.AdminACL'

    config.include('example_api.models')
    config.include('nefertari.view')
    config.include('nefertari.elasticsearch')

    enable_selfalias(config, "username")

    if Settings.asbool('debug'):
        log.warning('*** DEBUG DEBUG DEBUG mode ***')
        config.add_tween('nefertari.tweens.get_tunneling')

    if Settings.asbool('cors.enable'):
        config.add_tween('nefertari.tweens.cors')

    if Settings.asbool('ssl_middleware.enable'):
        config.add_tween('nefertari.tweens.ssl')

    if Settings.asbool('request_timing.enable'):
        config.add_tween('nefertari.tweens.request_timing')

    if Settings.asbool('auth', False):
        config.add_request_method(
            'example_api.models.User.get_authuser_by_userid', 'user', reify=True)
    else:
        log.warning('*** USER AUTHENTICATION IS DISABLED ! ***')
        config.add_request_method(
            'example_api.models.User.get_unauth_user', 'user', reify=True)

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

    config.commit()
    initialize()

    return config.make_wsgi_app()


def includeme(config):
    log.info("%s %s" % (APP_NAME, __version__))

    bootstrap(config)

    config.scan(package='example_api.views')

    config.add_route('login', '/login')
    config.add_view(
        view='example_api.views.account.TicketAuthenticationView',
        route_name='login', attr='login', request_method='POST')

    config.add_route('logout', '/logout')
    config.add_view(
        view='example_api.views.account.TicketAuthenticationView',
        route_name='logout', attr='logout')

    config.add_route('account', '/account')
    config.add_view(
        view='example_api.views.account.TicketAuthenticationView',
        route_name='account', attr='register', request_method='POST')

    create_resources(config)


def create_resources(config):
    from example_api.models import User, Story
    root = config.get_root_resource()

    user = root.add(
        'user', 'users',
        id_name='user_' + User.pk_field(),
        factory="example_api.acl.UserACL")

    user.add('group', 'groups',
             view='example_api.views.users.UserAttributesView',
             factory="example_api.acl.UserACL")
    user.add('setting', 'settings',
             view='example_api.views.users.UserAttributesView',
             factory="example_api.acl.UserACL")
    user.add('profile',
             view='example_api.views.users.UserProfileView',
             factory="example_api.acl.UserACL")

    root.add('s_one', 's', factory='nefertari.acl.GuestACL')

    root.add(
        'story', 'stories',
        id_name='story_' + Story.pk_field(),
        factory="example_api.acl.StoryACL")


def initialize():
    from example_api.models import User
    import transaction
    log.info('Initializing')
    try:
        s_user = Settings['system.user']
        s_pass = Settings['system.password']
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
