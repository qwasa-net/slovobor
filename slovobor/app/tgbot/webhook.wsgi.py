import datetime
import json
import logging
import re

import tgbot.messages
import tgbot.tasks
from settings import *


def application(env, start_response):
    """
    uwsgi handler 
    # How to set TGBot webhook:
    # > curl -F "url=https://url/path/tghook.py" "https://api.telegram.org/bot<TOKEN>/setWebhook"
    """

    if TG_WEBHOOK_TOKEN not in env.get("REQUEST_URI", ""):
        logging.debug("%s %s", TG_WEBHOOK_TOKEN, env.get("REQUEST_URI", "[REQUEST_URI]"))
        return error400(start_response)

    data = read_data(env)
    if not data:
        return error400(start_response)

    message = parse_data(data)
    logging.debug("message=%s", message)
    if not message:
        return error400(start_response)

    _ok, reply = process_message(message)

    if reply is not None:  # instant reply
        data = {"method": "sendMessage",
                "chat_id": message.get("chatid"),
                "reply_to_message_id": message.get("msgid"),
                "text": reply[:4096],
                "parse_mode": "Markdown"}
        rsp = json.dumps(data)
    else:
        rsp = """{}"""

    start_response('200 OK', [('Content-Type', 'application/json'),
                              ('Access-Control-Allow-Origin', '*'),
                              ('Cache-Control', 'no-cache, must-revalidate'),
                              ('Expires', 'Fri, 1 Jan 1999 01:01:01 GMT'), ])

    return [bytes(rsp, 'utf-8', 'ignore')]


def error400(start_response, msg="huh?"):
    start_response('400 BAD REQUEST', [('Content-Type', 'plain/text')])
    return [bytes(msg, 'utf-8', 'ignore')]


def read_data(env):
    try:
        request_body_size = int0(env.get('CONTENT_LENGTH', 0))
        request_body = env['wsgi.input'].read(request_body_size)
        return json.loads(request_body.decode('utf-8', errors='ignore'))
    except Exception as x:
        logging.error("read failed: %s", x)


def parse_data(data):
    message = data.get("message")
    if not message:
        return None
    msgid = message.get("message_id")
    date = message.get("date")
    chat = message.get("chat", {})
    chatid = chat.get("id")
    sender = message.get("from", {})
    lang = sender.get("language_code")
    userid = sender.get("id")
    first_name = sender.get('first_name')
    last_name = sender.get('last_name')
    username = sender.get("username")
    username0 = username or first_name or last_name or "user"
    fullname = " ".join(filter(lambda x: x, [username, first_name, last_name]))
    text0 = message.get("text")
    text = sstrip(text0)
    return locals()


TALK_START_RE = re.compile(r'^\s*(/start|help|.*\?|привет|hi|hello|!)\s*$', re.IGNORECASE)
TALK_WORD_RE = re.compile(r'^\s*\?+\s*(.+)', re.IGNORECASE | re.UNICODE)


def process_message(message):
    """
    process text message 
    -- reply instantly to /start,
    -- or call async task to get answer from delta engine
    """

    text = message.get("text0", "")

    # word posted
    mo = TALK_WORD_RE.search(text)
    if text and mo is not None:
        qword = sstrip(mo.group(1))
        logging.info("user=`%s#%s` word=`%s`", message.get("username0"), message.get("userid"), qword)

        if len(qword) > INPUT_MAX_LENGTH:
            return False, tgbot.messages.get('toomuch', data=message)

        tgbot.tasks.get_words_for_reply.apply_async(args=(qword, message,), countdown=1)
        return True, None

    # /start
    elif TALK_START_RE.search(text) is not None:
        # instant response
        logging.info("user=`%s#%s` start", message.get("username"), message.get("userid"))
        return True, tgbot.messages.get('start', data=message)
        # delayed response
        # tgbot.tasks.say_hello.apply_async(args=(message,))
        # return True, None

    # something unknown posted
    return False, tgbot.messages.get('mumble')
