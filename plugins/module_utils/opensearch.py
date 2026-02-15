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


def params_differ(local_params: dict[Any, Any], remote_params: dict[Any, Any], skip_keys: list[str] = []) -> bool:
    """Returns True if any record from local_params differs from corresponding record from remote_params."""
    for key, value in local_params.items():
        # Skip some specific parameters that function should not compare.
        if key in skip_keys:
            continue
        if remote_params.get(key, "") != value:
            return True
    return False


class OpenSearchModule(AnsibleModule):
    def __init__(self, **kwargs):
        self.api_prefix = kwargs.pop("api_prefix", "")
        super(OpenSearchModule, self).__init__(**kwargs)

        self.connection = Connection(self._socket_path)
        self.changed = False
        self.result = None

    def opensearch_request(
            self, data: dict | list | None, path: str, method: str
    ) -> dict[Any, Any] | None:
        """
        Perform an API request to the OpenSearch cluster.
        This method does error checking so method callers can trust the response.
        """
        try:
            if not path.startswith("/"):
                path = "/" + path

            code, response = self.connection.send_request(data, path, method)

            if code == 404:
                return None

            if code >= 400:
                self.fail_json(msg=f"HTTP Error occurred: {code} {response}")

            if response is None:
                self.fail_json(msg="Error: Empty response from the OpenSearch cluster.")

            return response
        except Exception as e:
            self.fail_json(msg=f"Exception caught: {to_text(e)}")

    def security_crud_sequence(
            self, api_object_parameters: dict[str, Any]
    ) -> Tuple[bool, dict[str, Any]]:
        """
        Performs create/update/delete sequence for the Security API objects.
        Needed CRUD operation is detected based on existence of the object in the cluster.

        Args:
            api_object_parameters: Dictionary of object parameters that will be used as request body
                on create or update operations.

        Returns:
            tuple of 'changed_flag' (True if the object was modified, False otherwise) and
            'module_result' (dictionary of result of the operations).
        """
        obj_name = self.params["name"]

        # Skip these keys when comparing parameters.
        user_specific_keys = ["password", "password_hash"]

        changed_flag = False
        module_result = None
        force_update = self.params.get("force", False)
        existent_objects = self.opensearch_request(None, self.api_prefix, "GET")
        existent_object = existent_objects.get(obj_name, None)
        if self.params["state"] == "present":
            if not existent_object:
                if not self.check_mode:
                    self.opensearch_request(
                        api_object_parameters, self.api_prefix + obj_name, "PUT"
                    )
                module_result = {"message": f"'{obj_name}' was created.", "status": "CREATED"}
                changed_flag = True
            elif force_update or params_differ(api_object_parameters, existent_object, user_specific_keys):
                patch_body = [
                    {
                        "op": "replace",
                        "path": "/" + obj_name,
                        "value": api_object_parameters,
                    }
                ]
                if not self.check_mode:
                    self.opensearch_request(patch_body, self.api_prefix, "PATCH")
                module_result = {"message": f"'{obj_name}' was updated.", "status": "UPDATED"}
                changed_flag = True
            else:
                module_result = {"message": f"'{obj_name}' is up to date.", "status": "OK"}
        elif self.params["state"] == "absent":
            if existent_object:
                if not self.check_mode:
                    self.opensearch_request(None, self.api_prefix + obj_name, "DELETE")
                module_result = {"message": f"'{obj_name}' was deleted.", "status": "DELETED"}
                changed_flag = True
            else:
                module_result = {"message": f"'{obj_name}' not found.", "status": "OK"}
        return changed_flag, module_result
