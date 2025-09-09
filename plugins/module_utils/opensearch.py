#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type  # pylint: disable=C0103

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib  # type: ignore
from typing import Any, Dict, List, Optional, Tuple, Union
import traceback

OPENSEARCH_IMPORT_FAIL = None
try:
    from opensearchpy import OpenSearch, OpenSearchException

    OPENSEARCH_MODULE_OK = True
except ImportError:
    OPENSEARCH_MODULE_OK = False
    OPENSEARCH_IMPORT_FAIL = traceback.format_exc()

OBJECT_FIELD_MAPPING = {
    'user': 'username',
    'role_mapping': 'role'
}


def opensearch_auth_argument_spec():
    return dict(
        api_host=dict(
            type='str',
            fallback=(env_fallback, ['OPENSEARCH_API_HOST']),
        ),
        api_port=dict(
            type='int',
            fallback=(env_fallback, ['OPENSEARCH_API_PORT']),
        ),
        api_username=dict(
            type='str',
            fallback=(env_fallback, ['OPENSEARCH_API_USERNAME']),
        ),
        api_password=dict(
            type='str',
            no_log=True,
            fallback=(env_fallback, ['OPENSEARCH_API_PASSWORD']),
        ),
        api_use_ssl=dict(
            type='bool',
            default=True,
            fallback=(env_fallback, ['OPENSEARCH_API_USE_SSL']),
        ),
        api_verify_certs=dict(
            type='bool',
            default=True,
            fallback=(env_fallback, ['OPENSEARCH_API_VERIFY_CERTS']),
        ),
        api_admin_cert_file=dict(
            type='str',
            fallback=(env_fallback, ['OPENSEARCH_API_ADMIN_CERT_FILE']),
        ),
        api_admin_key_file=dict(
            type='str',
            fallback=(env_fallback, ['OPENSEARCH_API_ADMIN_KEY_FILE']),
        ),
    )


class OpenSearchModule(AnsibleModule):
    def __init__(self, **kwargs):
        argument_spec = kwargs.pop('argument_spec', {})
        argument_spec.update(opensearch_auth_argument_spec())
        required_together = kwargs.pop('required_together', [])
        required_together.extend([
            ('api_username', 'api_password'),
            ('api_admin_cert_file', 'api_admin_key_file'),
        ])
        required_one_of = kwargs.pop('required_one_of', [])
        required_one_of.extend([
            ('api_password', 'api_admin_cert_file'),
        ])

        super(OpenSearchModule, self).__init__(
            argument_spec=argument_spec,
            required_together=required_together,
            required_one_of=required_one_of,
            **kwargs
        )

        if not OPENSEARCH_MODULE_OK:
            self.fail_json(msd=missing_required_lib('opensearchpy'), exception=OPENSEARCH_IMPORT_FAIL)

        self.os = self._connect()
        try:
            self.os.info()
        except Exception as e:
            self.fail_json(msg='%s' % e, exception=traceback.format_exc())

        self.changed = False
        self.result = None

    def _connect(self) -> OpenSearch:
        connection_params = {
            'hosts': [{
                'host': self.params['api_host'],
                'port': self.params['api_port']
            }],
            'use_ssl': self.params['api_use_ssl'],
            'verify_certs': self.params['api_verify_certs'],
        }

        if self.params['api_admin_key_file'] and self.params['api_admin_cert_file']:
            connection_params.update({
                'client_cert': self.params['api_admin_cert_file'],
                'client_key': self.params['api_admin_key_file'],
            })
        else:
            connection_params.update({
                'http_auth': (
                    self.params['api_username'],
                    self.params['api_password'],
                ),
            })

        return OpenSearch(**connection_params)

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
