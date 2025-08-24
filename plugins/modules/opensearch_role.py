#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

DOCUMENTATION = """
    module: opensearch_role
    author: Castor Sky (@castorsky)
    version_added: "0.1.0"
    short_description: Manage roles in OpenSearch cluster.
    description:
      - Module manages (creates/updates/deletes) roles in OpenSearch cluster.
    options:
      name:
        description: Value specified here is appended to the Hello message.
        type: str
"""

EXAMPLES = """
# sample_module module example

- name: Display a hello message
  ansible.builtin.debug:
    msg: "{{ 'ansible-creator' | sample_module }}"
"""

__metaclass__ = type  # pylint: disable=C0103

from typing import TYPE_CHECKING
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib  # type: ignore

# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=12877, stdout_to_server=True, stderr_to_server=True)

if TYPE_CHECKING:
    from typing import Callable

OPENSEARCH_IMPORT_FAIL = None
try:
    from opensearchpy import OpenSearch

    OPENSEARCH_MODULE_OK = True
except ImportError:
    OPENSEARCH_MODULE_OK = False
    OPENSEARCH_IMPORT_FAIL = traceback.format_exc()


def main() -> None:
    """entry point for module execution"""
    argument_spec = dict(
        api_host=dict(type='str',
                      # required=True,
                      fallback=(env_fallback, ['OPENSEARCH_API_HOST']),
                      ),
        api_port=dict(type='int',
                      # required=True,
                      fallback=(env_fallback, ['OPENSEARCH_API_PORT']),
                      ),
        api_username=dict(type='str',
                          # required=True,
                          fallback=(env_fallback, ['OPENSEARCH_API_USERNAME']),
                          ),
        api_password=dict(type='str',
                          # required=True,
                          no_log=True,
                          fallback=(env_fallback, ['OPENSEARCH_API_PASSWORD']),
                          ),
        api_use_ssl=dict(type='bool',
                         default=True,
                         fallback=(env_fallback, ['OPENSEARCH_API_USE_SSL']),
                         ),
        api_verify_certs=dict(type='bool',
                              default=True,
                              fallback=(env_fallback, ['OPENSEARCH_API_VERIFY_CERTS']),
                              ),
        name=dict(type='str', required=True),
        description=dict(type='str', default=''),
        cluster_permissions=dict(type='list', default=[]),
        index_permissions=dict(type='list', default=[]),
        tenant_permissions=dict(type='list', default=[]),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not OPENSEARCH_MODULE_OK:
        module.fail_json(msd=missing_required_lib('opensearchpy'), exception=OPENSEARCH_IMPORT_FAIL)

    c = OpenSearch(
        hosts=[{'host': module.params['api_host'], 'port': module.params['api_port']}],
        http_auth=(
            module.params['api_username'],
            module.params['api_password'],
        ),
        use_ssl=module.params['api_use_ssl'],
        verify_certs=module.params['api_verify_certs'],
    )
    role_name = module.params['name']
    role_parameters = {
        'description': module.params['description'],
        'cluster_permissions': module.params['cluster_permissions'],
        'index_permissions': module.params['index_permissions'],
        'tenant_permissions': module.params['tenant_permissions'],
    }

    changed_flag = False
    module_result = None
    existent_roles = c.security.get_roles()
    if module.params['state'] == 'present':
        if role_name not in existent_roles:
            module_result = c.security.create_role(
                role=role_name,
                body=role_parameters,
            )
            changed_flag = True
        else:
            role_differs = False
            for p in role_parameters:
                if role_parameters[p] != existent_roles[role_name].get(p, ''):
                    role_differs = True
                    break
            if role_differs:
                module_result = c.security.patch_roles(
                    body=[{
                        'op': 'replace',
                        'path': f'/{role_name}',
                        'value': role_parameters,
                    }]
                )
                changed_flag = True
    elif module.params['state'] == 'absent':
        if role_name in existent_roles:
            module_result = c.security.delete_role(
                role=role_name,
            )
            changed_flag = True

    result = {'changed': changed_flag, 'content': module_result}
    module.exit_json(**result)


if __name__ == '__main__':
    main()
