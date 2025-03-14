from models.insider import Insider
from utils.decorators.check_sign import check_sign
from utils.decorators.request_limit import request_limit
from . import api
from utils.decorators.stopped import stopped

@api.route('/insiders/<string:open_id>', methods=['GET'])
@check_sign(set())
@request_limit(15)
@stopped(message='暂不开放')
def handle_insider_detail(open_id: str):
    insider: Insider = Insider.query.get(open_id)
    if not insider:
        return {
            'code': 0,
            'data': {
                'status': -3
            }
        }
    return {
        'code': 0,
        'data': insider.serialize()
    }
