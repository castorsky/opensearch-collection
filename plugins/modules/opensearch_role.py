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

from ansible_collections.castorsky.opensearch.plugins.module_utils.opensearch import OpenSearchModule


def main() -> None:
    module_argument_spec = dict(
        name=dict(type='str', required=True),
        cluster_permissions=dict(type='list', default=[]),
        index_permissions=dict(type='list', default=[]),
        tenant_permissions=dict(type='list', default=[]),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        description=dict(type='str', default=''),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
    )

    role_name = module.params['name']
    role_parameters = {
        'cluster_permissions': module.params['cluster_permissions'],
        'index_permissions': module.params['index_permissions'],
        'tenant_permissions': module.params['tenant_permissions'],
        'description': module.params['description'],
    }

    changed_flag = False
    module_result = None
    existent_roles = module.os.security.get_roles()

    if module.params['state'] == 'present':
        if role_name not in existent_roles:
            module_result = module.os.security.create_role(
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
                module_result = module.os.security.patch_roles(
                    body=[{
                        'op': 'replace',
                        'path': f'/{role_name}',
                        'value': role_parameters,
                    }]
                )
                changed_flag = True
    elif module.params['state'] == 'absent':
        if role_name in existent_roles:
            module_result = module.os.security.delete_role(
                role=role_name,
            )
            changed_flag = True

    result = {'changed': changed_flag, 'content': module_result}
    module.exit_json(**result)


if __name__ == '__main__':
    main()
