# -*- coding: utf-8 -*-
#
# This file is part of eduMFA. eduMFA is a fork of privacyIDEA which was forked from LinOTP.
# Copyright (c) 2024 eduMFA Project-Team
# Previous authors by privacyIDEA project:
#
# 2015 Cornelius Kölbel, <cornelius@privacyidea.org>
#
# (c) Cornelius Kölbel
#
# This code is free software; you can redistribute it and/or
# modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
# License as published by the Free Software Foundation; either
# version 3 of the License, or any later version.
#
# This code is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU AFFERO GENERAL PUBLIC LICENSE for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
__doc__ = """This endpoint is used to create, update, list and delete SMTP
server definitions. SMTP server definitions can be used for several purposes
like
EMail-Token, SMS Token with SMTP gateway, notification like PIN handler and
registration.

The code of this module is tested in tests/test_api_smtpserver.py
"""
import logging

from flask import Blueprint, current_app, g, request
from flask_babel import gettext as _

from edumfa.lib.smtpserver import (
    add_smtpserver,
    delete_smtpserver,
    list_smtpservers,
    send_or_enqueue_email,
)

from ..api.lib.prepolicy import check_base_action, prepolicy
from ..lib.crypto import FAILED_TO_DECRYPT_PASSWORD, decryptPassword
from ..lib.log import log_with
from ..lib.policy import ACTION
from ..lib.utils import is_true
from .lib.utils import getParam, required, send_result

log = logging.getLogger(__name__)

smtpserver_blueprint = Blueprint("smtpserver_blueprint", __name__)


@smtpserver_blueprint.route("/<identifier>", methods=["POST"])
@prepolicy(check_base_action, request, ACTION.SMTPSERVERWRITE)
@log_with(log)
def create(identifier=None):
    """
    This call creates or updates an SMTP server definition.

    :param identifier: The unique name of the SMTP server definition
    :param server: The FQDN or IP of the mail server
    :param port: The port of the mail server
    :param username: The mail username for authentication at the SMTP server
    :param password: The password for authentication at the SMTP server
    :param tls: If the server should do TLS
    :param description: A description for the definition
    """
    param = request.all_data
    server = getParam(param, "server", required)
    port = int(getParam(param, "port", default=25))
    username = getParam(param, "username", default="")
    password = getParam(param, "password", default="")
    sender = getParam(param, "sender", default="")
    tls = is_true(getParam(param, "tls", default=False))
    description = getParam(param, "description", default="")
    timeout = int(getParam(param, "timeout") or 10)
    enqueue_job = is_true(getParam(param, "enqueue_job", default=False))

    r = add_smtpserver(
        identifier,
        server,
        port=port,
        username=username,
        password=password,
        tls=tls,
        description=description,
        sender=sender,
        timeout=timeout,
        enqueue_job=enqueue_job,
    )

    g.audit_object.log({"success": r > 0, "info": r})
    return send_result(r > 0)


@smtpserver_blueprint.route("/", methods=["GET"])
@log_with(log)
@prepolicy(check_base_action, request, ACTION.SMTPSERVERREAD)
def list_smtpservers_api():
    """
    This call gets the list of SMTP server definitions
    """
    res = list_smtpservers()
    g.audit_object.log({"success": True})
    return send_result(res)


@smtpserver_blueprint.route("/<identifier>", methods=["DELETE"])
@prepolicy(check_base_action, request, ACTION.SMTPSERVERWRITE)
@log_with(log)
def delete_server(identifier=None):
    """
    This call deletes the specified SMTP server configuration

    :param identifier: The unique name of the SMTP server definition
    """
    r = delete_smtpserver(identifier)

    g.audit_object.log({"success": r > 0, "info": r})
    return send_result(r > 0)


@smtpserver_blueprint.route("/send_test_email", methods=["POST"])
@prepolicy(check_base_action, request, ACTION.SMTPSERVERWRITE)
@log_with(log)
def test():
    """
    Test the email configuration
    :return:
    """
    param = request.all_data
    identifier = getParam(param, "identifier", required)
    server = getParam(param, "server", required)
    port = int(getParam(param, "port", default=25))
    username = getParam(param, "username", default="")
    password = getParam(param, "password", default="")
    sender = getParam(param, "sender", default="")
    tls = is_true(getParam(param, "tls", default=False))
    recipient = getParam(param, "recipient", required)
    timeout = int(getParam(param, "timeout") or 10)
    enqueue_job = is_true(getParam(param, "enqueue_job", default=False))

    s = dict(
        identifier=identifier,
        server=server,
        port=port,
        username=username,
        password=password,
        sender=sender,
        tls=tls,
        timeout=timeout,
        enqueue_job=enqueue_job,
    )
    r = send_or_enqueue_email(
        s,
        recipient,
        "Test Email from eduMFA",
        "This is a test email from eduMFA. "
        "The configuration {} is working.".format(identifier),
    )

    g.audit_object.log({"success": r > 0, "info": r})
    return send_result(r > 0)
