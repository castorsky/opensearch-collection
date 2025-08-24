#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

DOCUMENTATION = """
    module: opensearch_tenant
    author: Castor Sky (@castorsky)
    version_added: "0.1.0"
    short_description: Manage tenants in OpenSearch cluster.
    description:
      - Module manages (creates/updates/deletes) tenants in OpenSearch cluster.
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
# pydevd_pycharm.settrace('localhost', port=12499, stdout_to_server=True, stderr_to_server=True)

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
    tenant_name = module.params['name']
    tenant_description = module.params['description']

    # Get tenants
    changed_flag = False
    module_result = None
    existent_tenants = c.security.get_tenants()
    if module.params['state'] == 'present':
        if tenant_name not in existent_tenants:
            module_result = c.security.create_tenant(
                tenant=tenant_name,
                body={
                    'description': tenant_description,
                }
            )
            changed_flag = True
        elif tenant_description != existent_tenants[tenant_name].get('description', ''):
            module_result = c.security.patch_tenants(
                body=[{
                    'op': 'replace',
                    'path': f'/{tenant_name}',
                    'value': {
                        'description': tenant_description,
                    }
                }]
            )
            changed_flag = True
    elif module.params['state'] == 'absent':
        if tenant_name in existent_tenants:
            module_result = c.security.delete_tenant(
                tenant=tenant_name,
            )
            changed_flag = True

    result = {'changed': changed_flag, 'content': module_result}
    module.exit_json(**result)


if __name__ == '__main__':
    main()
