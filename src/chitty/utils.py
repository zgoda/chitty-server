from typing import Mapping, Optional


def error_response(reason: str, message: Optional[str] = None) -> Mapping[str, str]:
    return {
        'status': 'error',
        'error': {
            'reason': reason,
            'message': message or '',
        }
    }
