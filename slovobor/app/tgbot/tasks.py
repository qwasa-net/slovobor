import logging
import random

from celery import Celery

import slovobor
import tgbot.messages
import tgbot.poster
from settings import *

app = Celery('slovobor', broker=CELERY_BROKER, include=['tgbot.tasks'])
app.conf.update(ignore_result=True,)


@app.task
def get_words_for_reply(qword, message):

    words, count, count_txt = None, 0, 0

    try:
        cword = slovobor.clean_word(qword)
        words_line, count = slovobor.get_words(cword, min_length=4)
    except Exception as x:
        logging.error("slovobor error: %s `%s`", x, qword)
        return False

    logging.info("user=`%s#%s` word=`%s` → %s", message.get("username"), message.get("userid"), qword, count)

    if count > 0:

        template = random.choice(tgbot.messages.MESSAGES[LANG]["reply"])

        words_list = list(map(sstrip, words_line.split(",")))
        words_list.sort(key=lambda x: (-len(x), x))
        words = ", ".join(words_list[:TG_MAX_RESULTS])
        if count > TG_MAX_RESULTS:
            count_txt = "%s из %s" % (TG_MAX_RESULTS, count)
        else:
            count_txt = count

    else:
        template = random.choice(tgbot.messages.MESSAGES[LANG]["reply0"])
        words = ""

    reply = template.format(words=words, qword=qword, cword=cword, count=count_txt, **message)

    rc = tgbot.poster.post_message(reply, message["chatid"], message["msgid"])
    return rc


@app.task
def say_hello(message):

    template = random.choice(tgbot.messages.MESSAGES[LANG]["start"])
    reply = template.format(**message)

    rc = tgbot.poster.post_message(reply, message["chatid"], message["msgid"])
    return rc
