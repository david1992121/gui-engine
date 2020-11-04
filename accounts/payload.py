"""
Handlers for JWT
"""


def jwt_response_payload_handler(token, user=None, request=None):
    """Handler for JWT Payload"""
    return {
        'token': token,
        'user': user
    }
