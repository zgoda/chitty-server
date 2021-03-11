from typing import Mapping, Optional, Union


def error_response(
            reason: str, message: Optional[str] = None
        ) -> Mapping[str, Union[str, dict]]:
    """Build error response structure.

    :param reason: error reason
    :type reason: str
    :param message: error message, defaults to None
    :type message: Optional[str], optional
    :return: error response structure
    :rtype: Mapping[str, Union[str, dict]]
    """
    return {
        'status': 'error',
        'error': {
            'reason': reason,
            'message': message or '',
        }
    }
