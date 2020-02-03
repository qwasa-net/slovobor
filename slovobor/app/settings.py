import re
import os

_cfg = {}
_cfg_filename = os.environ.get("SLOVOBOR_CONFIG_FILE")

if _cfg_filename:
    try:
        import json
        _cfg = json.load(open(_cfg_filename, "r"))
    except Exception as _:
        raise  # log and go on?

# logging
DEBUG_LOG = _cfg.get("DEBUG_LOG", os.environ.get("SLOVOBOR_DEBUG_LOG", None))
DEBUG_LOG_FORMAT = _cfg.get('DEBUG_LOG_FORMAT', '%(asctime)s [%(levelname)s] @%(module)s::%(funcName)s %(message)s')
DEBUG_LOG_DATEFORMAT = _cfg.get('DEBUG_LOG_DATEFORMAT', '%y-%m-%d %H:%M:%S')

if DEBUG_LOG:
    import logging
    logging.basicConfig(filename=DEBUG_LOG,
                        format=DEBUG_LOG_FORMAT,
                        datefmt=DEBUG_LOG_DATEFORMAT,
                        level=logging.DEBUG)

# database
DB_HOST = _cfg.get("DB_HOST", os.environ.get("SLOVOBOR_DB_HOST", "127.0.0.1"))
DB_UNIX = _cfg.get("DB_UNIX", os.environ.get("SLOVOBOR_DB_UNIX", None))
DB_NAME = _cfg.get("DB_NAME", os.environ.get("SLOVOBOR_DB_NAME", "db"))
DB_USER = _cfg.get("DB_USER", os.environ.get("SLOVOBOR_DB_USER", "user"))
DB_PASS = _cfg.get("DB_PASS", os.environ.get("SLOVOBOR_DB_PASS", "password"))

# input / output
LANG = _cfg.get("LANG", 1)  # 1=RU, 2=EN, 3=RU+EN
INPUT_MAX_LENGTH = _cfg.get("INPUT_MAX_LENGTH", 40)
MIN_LENGTH = _cfg.get("MIN_LENGTH", 3)
MAX_RESULTS = _cfg.get("MAX_RESULTS", 1999)

# TG tokens
TG_BOT_TOKEN = _cfg.get("TG_BOT_TOKEN", "")
TG_WEBHOOK_TOKEN = _cfg.get("TG_WEBHOOK_TOKEN", "")
TG_ADMIN_ID = _cfg.get("TG_ADMIN_ID")
TG_API_URL = "https://api.telegram.org/bot{token}/{cmd}"

#
TG_BOT_USE_REDIS = "/home/slovobor.tktk.in/_redis.sock"
TG_BOT_USE_REDIS_DB = 1

TG_INPUT_MAX_LENGTH = _cfg.get("TG_INPUT_MAX_LENGTH", INPUT_MAX_LENGTH)
TG_MIN_LENGTH = _cfg.get("TG_MIN_LENGTH", 4)
TG_MAX_RESULTS = _cfg.get("TG_MAX_RESULTS", 100)

#
CELERY_BROKER = "redis+socket:///home/slovobor.tktk.in/_redis.sock"
CELERY_ALWAYS_EAGER = False


def int0(i, fallback=0):
    try:
        return int(i)
    except Exception:
        return fallback

sstrip_re = re.compile(r'\s+', re.I | re.U)


def sstrip(s, m=None):
    s = sstrip_re.sub(' ', s or '').strip()
    if m:
        return s[:m]
    return s
