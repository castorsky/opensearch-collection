#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=C0103

from ansible.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib  # type: ignore
from typing import Any, Dict, List, Optional, Tuple, Union
from ansible.module_utils.common.text.converters import to_text


class OpenSearchModule(AnsibleModule):
    def __init__(self, **kwargs):
        super(OpenSearchModule, self).__init__(**kwargs)

        self.connection = Connection(self._socket_path)
        self.changed = False
        self.result = None

    def opensearch_request(self, data: dict, path: str, method: str) -> dict[Any, Any] | None:
        """
        Perform an API request to the OpenSearch cluster.
        This method does error checking so method callers can trust the response.
        """
        try:
            if not path.startswith("/"):
                path = "/" + path

            code, response = self.connection.send_request(data, path, method)

            if code >= 400:
                self.fail_json(msg=f"HTTP Error occurred: {code} {response}")
            
            if response is None:
                self.fail_json(msg="Error: Empty response from the OpenSearch cluster.")

            return response
        except Exception as e:
            self.fail_json(msg=f"Exception caught: {to_text(e)}")
