def success_uri(uri):
    return uri is not None


def gen_eq_p(a, b):
    def __eq_p():
        return a == b


def on_fallback(fn, ffb, fallback_p, success_p):
    def __on_fallback(*args, **kwargs):
        rtv = fn(*args, **kwargs)
        if success_p(rtv):
            return rtv
        elif fallback_p():
            return ffb(*args, **kwargs)
        else:
            return rtv

    return __on_fallback


def const(value):
    def __const(*args, **kwargs):
        return value

    return __const
