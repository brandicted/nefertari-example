from nefertari.authentication.views import (
    TicketAuthenticationView as NefTicketAuthenticationView)

from example_api.models import User


class TicketAuthenticationView(NefTicketAuthenticationView):
    """ Not implemented by default NefTicketAuthenticationView:

    * Check for user to be active on register
    * Making user 'status' being 'active' on register
    * Checking user 'status' is not 'blocked', 'inactive' on login
    * Calling user.on_login()
    """
    _model_class = User
