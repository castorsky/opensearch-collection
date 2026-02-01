# (c) 2026 Castor Sky <csky57@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
author:
- Castor Sky (@castorsky)
name : opensearch
short_description: HttpApi Plugin for OpenSearch REST API
description:
  - This HttpApi plugin provides methods to connect to OpenSearch over HTTP(S)-based APIs.
options:
  opensearch_http_headers:
    type: dict
    description:
      - A dictionary of additional HTTP headers to be sent with every request to the OpenSearch API.
      - These headers are applied first, and can be overridden by plugin-specific headers like 'Authorization'.
    vars:
      - name: ansible_opensearch_http_headers
"""

import json

from ansible.module_utils.common.text.converters import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.connection import ConnectionError
from urllib.error import HTTPError

BASE_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


class HttpApi(HttpApiBase):
    def set_become(self, become_context):
        """There is no privilege elevation method in OpenSearch API"""
        pass

    def send_request(self, data, path="/", method="POST"):
        try:
            headers = BASE_HEADERS.copy()
            custom_headers = self.get_option("opensearch_http_headers")
            if isinstance(custom_headers, dict):
                headers.update(custom_headers)

            request_data = json.dumps(data) if data else "{}"

            self._display_request(method=method)
            response, response_data = self.connection.send(
                path, request_data, method=method, headers=headers
            )

            response_value = self._get_response_value(response_data)

            return response.getcode(), self._response_to_json(response_value)
        except AnsibleConnectionFailure as e:
            self.connection.queue_message("vvv", "AnsibleConnectionFailure: %s" % e)
            raise e
        except HTTPError as e:
            self.connection.queue_message("vvv", "HTTPError: %s" % e)
            return e.code, to_text(e.read())

    def _display_request(self, method="POST"):
        self.connection.queue_message(
            "vvvv", "Web Services: %s %s" % (method, self.connection._url)
        )

    def _get_response_value(self, response_data):
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            raise ConnectionError("Invalid JSON response: %s" % response_text)
