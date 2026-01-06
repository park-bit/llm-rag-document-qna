
import time

_MAX_PER_MIN = 30
_state = {}

def allow_request(client_ip: str) -> bool:
    now = int(time.time())
    window = now // 60
    rec = _state.get(client_ip)
    if rec is None or rec[0] != window:
        _state[client_ip] = [window, 1]
        return True
    else:
        if rec[1] < _MAX_PER_MIN:
            rec[1] += 1
            return True
        else:
            return False
