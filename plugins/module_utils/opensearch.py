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

    def default_passthrough(self, api_group: str, object_type: str, object_params: List[str]) -> Tuple[
        bool, Union[Dict, None]]:
        changed_flag = False
        module_result = None

        object_name = self.params['name']
        # Sometimes (e.g. in 'role_mapping') the name field is not equal
        # the object type and need to be mutated.
        object_name_field = object_type if object_type != 'role_mapping' else 'role'
        object_parameters = {param: self.params[param] for param in object_params}

        api_group_callable = getattr(self.os, api_group)
        multiple_objects_getter = getattr(api_group_callable, f'get_{object_type}s')
        object_creator = getattr(api_group_callable, f'create_{object_type}')
        multiple_objects_patcher = getattr(api_group_callable, f'patch_{object_type}s')
        object_remover = getattr(api_group_callable, f'delete_{object_type}')

        existent_objects = multiple_objects_getter()

        if self.params['state'] == 'present':
            if object_name not in existent_objects:
                creator_args = {
                    object_name_field: object_name,
                    'body': object_parameters,
                }
                module_result = object_creator(**creator_args)
                changed_flag = True
            else:
                object_differs = False
                for p in object_parameters:
                    if object_parameters[p] != existent_objects[object_name].get(p, ''):
                        object_differs = True
                        break
                if object_differs:
                    module_result = multiple_objects_patcher(
                        body=[{
                            'op': 'replace',
                            'path': f'/{object_name}',
                            'value': object_parameters,
                        }]
                    )
                    changed_flag = True
        elif self.params['state'] == 'absent':
            if object_name in existent_objects:
                remover_args = {
                    object_name_field: object_name,
                }
                module_result = object_remover(**remover_args)
                changed_flag = True

        return changed_flag, module_result
