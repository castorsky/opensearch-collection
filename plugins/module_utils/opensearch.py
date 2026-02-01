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

# Remap some field names to synonyms to match OpenSearch API.
OBJECT_FIELD_MAPPING = {
    'user': 'username',
    'role_mapping': 'role'
}


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
            code, response = self.connection.send_request(data, path, method)

            if code >= 400:
                self.fail_json(msg=f'HTTP Error occurred: {code} {response}')

            return response
        except Exception as e:
            self.fail_json(msg=f'Exception caught: {to_text(e)}')

    def default_sequence(self, api_group: str, object_type: str, object_params: List[str]):
        self._setup_executor(api_group, object_type, object_params)

        if self.params['state'] == 'present':
            if self._object_name not in self._existent_objects:
                self._create_absent_object()
            else:
                self._update_existent_object()
        elif self.params['state'] == 'absent':
            if self._object_name in self._existent_objects:
                self._remove_existing_object()

    def user_sequence(self, api_group: str, object_type: str, object_params: List[str]):
        self._setup_executor(api_group, object_type, object_params)

        user_parameters_with_pwd = self._object_parameters.copy()
        if self.params['password']:
            user_parameters_with_pwd['password'] = self.params['password']
        elif self.params['password_hash']:
            user_parameters_with_pwd['password_hash'] = self.params['password_hash']

        if self.params['state'] == 'present':
            if self._object_name not in self._existent_objects:
                # Do not want to define one more function with one changed line.
                # It seems that self._object_parameter is used the last time
                # so it is safe to rewrite it with password parameters.
                self._object_parameters = user_parameters_with_pwd
                self._create_absent_object()
            else:
                self._update_existent_user(user_parameters_with_pwd)
        elif self.params['state'] == 'absent':
            if self._object_name in self._existent_objects:
                self._remove_existing_object()

    def _setup_executor(self, api_group, object_type, object_params):
        self._object_name = self.params['name']

        self._object_name_field = OBJECT_FIELD_MAPPING[object_type] \
            if object_type in OBJECT_FIELD_MAPPING else object_type

        self._object_parameters = {param: self.params[param] for param in object_params}

        # Get opensearch_py methods to work with this particular object type (role, user, etc.).
        api_group_callable = getattr(self.os, api_group)
        self._multiple_objects_getter = getattr(api_group_callable, f'get_{object_type}s')
        self._object_creator = getattr(api_group_callable, f'create_{object_type}')
        self._multiple_objects_patcher = getattr(api_group_callable, f'patch_{object_type}s')
        self._object_remover = getattr(api_group_callable, f'delete_{object_type}')

        self._existent_objects = self._multiple_objects_getter()

    def _create_absent_object(self):
        creator_args = {
            self._object_name_field: self._object_name,
            'body': self._object_parameters,
        }
        self.result = self._object_creator(**creator_args)
        self.changed = True

    def _update_existent_object(self):
        object_differs = False
        for p in self._object_parameters:
            if self._object_parameters[p] != self._existent_objects[self._object_name].get(p, ''):
                object_differs = True
                break
        if object_differs:
            self.result = self._multiple_objects_patcher(
                body=[{
                    'op': 'replace',
                    'path': f'/{self._object_name}',
                    'value': self._object_parameters,
                }]
            )
            self.changed = True

    def _update_existent_user(self, user_parameters_with_pwd):
        user_differs = True if self.params['force'] else False
        for p in self._object_parameters:
            if self._object_parameters[p] != self._existent_objects[self._object_name].get(p, ''):
                user_differs = True
                break
        if user_differs:
            self.result = self._multiple_objects_patcher(
                body=[{
                    'op': 'replace',
                    'path': f'/{self._object_name}',
                    'value': user_parameters_with_pwd,
                }]
            )
            self.changed = True

    def _remove_existing_object(self):
        remover_args = {
            self._object_name_field: self._object_name,
        }
        self.result = self._object_remover(**remover_args)
        self.changed = True
