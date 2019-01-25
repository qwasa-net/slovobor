import logging
import urllib.parse

import slovobor
from settings import *

RSP_HEADERS = [('Content-Type', 'application/json'),
               ('Access-Control-Allow-Origin', '*'),
               ('Cache-Control', 'no-cache, must-revalidate'),
               ('Expires', 'Fri, 1 Jan 1999 01:01:01 GMT'), ]


def application(env, start_response):

    if DEBUG_LOG:
        logging.debug('%s %s', env.get('REMOTE_ADDR'), env.get('REQUEST_METHOD'))

    if env.get('REQUEST_METHOD') != "POST":
        logging.error("error 400: REQUEST_METHOD=%s", env.get('REQUEST_METHOD'))
        return error400(start_response)

    form = parse_input_form(env)

    qword = form.get('q')
    if qword is None or len(qword) > INPUT_MAX_LENGTH:
        logging.error("error 400: qword=`%s`; len=%s", str(qword), len(qword or ""))
        return error400(start_response)

    skip_offensive = form.get('o') == '1'
    only_nouns = form.get('n') == '1'

    try:
        cword = slovobor.clean_word(qword)
        words, count = slovobor.get_words(cword,
                                          skip_offensive=skip_offensive,
                                          only_nouns=only_nouns)
    except Exception as x:
        logging.error("slovobor error: %s `%s`", x, qword)
        return error400(start_response)

    if DEBUG_LOG:
        logging.debug('`%s` → %s: `%s`', qword, count, words)

    rsp = """{"q":"%s", "c":%i, "w":"%s"}""" % (qword, count, words or "")
    start_response('200 OK', RSP_HEADERS)
    return [bytes(rsp, 'utf-8', 'ignore')]


def error400(start_response, msg="huh?"):
    start_response('400 BAD REQUEST', [('Content-Type', 'plain/text')])
    return [bytes(msg, 'utf-8', 'ignore')]


def parse_input_form(env):

    form = {}

    try:
        request_body_size = int0(env.get('CONTENT_LENGTH', 0))
        request_body = env['wsgi.input'].read(request_body_size)

        posted_form = urllib.parse.parse_qs(request_body.decode('utf-8', 'ignore'),
                                            keep_blank_values=False,
                                            strict_parsing=False,
                                            encoding='utf-8',
                                            errors='ignore')

        for k in posted_form:
            form[k] = posted_form[k][0]

    except Exception as x:
        logging.error("input parsing failed: %s", x)

    return form
