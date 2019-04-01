import logging

import requests

from settings import *


def post_message(text, chat_id, reply_to=None):

    url = TG_API_URL.format(token=TG_BOT_TOKEN, cmd="sendMessage")

    data = {"chat_id": chat_id, "text": text[:4096], "parse_mode": "Markdown"}
    if reply_to is not None:
        data["reply_to_message_id"] = reply_to

    rq = requests.post(url, data=data)

    logging.info("@post_message %s, %s %s", chat_id, rq.status_code, url)
    return rq.status_code == 200
