#!/usr/bin/python
#
# External auth script for ejabberd that enable auth against MySQL db with
# use of custom fields and table. It works with hashed passwords.
# Inspired by Lukas Kolbe script.
# Released under GNU GPLv3
# Requires Python 2
# Author: iltl. Contact: iltl@free.fr
# Author: Candid Dauth <cdauth@cdauth.eu>
# Version: 2015-12-20

########################################################################
# DB Settings
# Just put your settings here.
########################################################################

import os


ext_host = os.environ['AUTH_EXT_HOST']


########################################################################
# Setup
########################################################################

import sys, logging, struct, requests

sys.stderr = open('/var/log/ejabberd/extauth_err.log', 'a')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='/var/log/ejabberd/extauth.log',
                    filemode='a')

logging.info('extauth script started, waiting for ejabberd requests')


class EjabberdInputError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


########################################################################
# Declarations
########################################################################

def ejabberd_in():
    logging.debug("trying to read 2 bytes from ejabberd:")

    input_length = sys.stdin.read(2)

    if len(input_length) is not 2:
        logging.debug("ejabberd sent us wrong things!")
        raise EjabberdInputError('Wrong input from ejabberd!')

    logging.debug('got 2 bytes via stdin: %s' % input_length)

    (size,) = struct.unpack('>h', input_length)
    logging.debug('size of data: %i' % size)

    income = sys.stdin.read(size).split(':')
    logging.debug("incoming data: %s" % income)

    return income


def ejabberd_out(bool):
    logging.debug("Ejabberd gets: %s" % bool)

    token = genanswer(bool)

    logging.debug("sent bytes: %#x %#x %#x %#x" % (ord(token[0]), ord(token[1]), ord(token[2]), ord(token[3])))

    sys.stdout.write(token)
    sys.stdout.flush()


def genanswer(bool):
    answer = 0
    if bool:
        answer = 1
    token = struct.pack('>hh', 2, answer)
    return token


def isuser(user, host):
    response = requests.get(url=ext_host + '/api/internal/chat/is_user', params={'user': user})
    if response.status_code == 200:
        return True
    else:
        return False


def auth(user, host, password):
    headers = {'Authorization': 'Bearer ' + password, 'Accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.get(url=ext_host + '/api/internal/chat/auth', headers=headers, params={'user': user})
    if response.status_code == 200:
        return True
    else:
        return False


def setpass(user, host, password):
    pass


def tryregister(user, host, password):
    pass


def removeuser(user, host):
    pass

def removeuser3(user, host, password):
    pass


########################################################################
# Main Loop
########################################################################

exitcode = 0

while True:
    logging.debug("start of infinite loop")

    try:
        ejab_request = ejabberd_in()
    except EOFError:
        break
    except Exception as e:
        logging.exception("Exception occured while reading stdin")
        raise

    logging.debug('operation: %s' % (":".join(ejab_request)))

    op_result = False
    try:
        if ejab_request[0] == "auth":
            op_result = auth(ejab_request[1], ejab_request[2], ejab_request[3])
        elif ejab_request[0] == "isuser":
            op_result = isuser(ejab_request[1], ejab_request[2])
        elif ejab_request[0] == "setpass":
            op_result = setpass(ejab_request[1], ejab_request[2], ejab_request[3])
        elif ejab_request[0] == "tryregister":
            op_result = tryregister(ejab_request[1], ejab_request[2], ejab_request[3])
        elif ejab_request[0] == "removeuser":
            op_result = removeuser(ejab_request[1], ejab_request[2])
        elif ejab_request[0] == "removeuser3":
            op_result = removeuser3(ejab_request[1], ejab_request[2], ejab_request[3])
    except Exception:
        logging.exception("Exception occured")

    ejabberd_out(op_result)
    logging.debug("successful" if op_result else "unsuccessful")

logging.debug("end of infinite loop")
logging.info('extauth script terminating')
sys.exit(exitcode)