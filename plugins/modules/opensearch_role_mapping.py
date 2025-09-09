#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

from readline import backend

DOCUMENTATION = """
    module: opensearch_user
    author: Castor Sky (@castorsky)
    version_added: "0.1.0"
    short_description: Manage users in OpenSearch cluster.
    description:
      - Module manages (creates/updates/deletes) users in OpenSearch cluster.
    options:
      name:
        description: Value specified here is appended to the Hello message.
        type: str
"""

EXAMPLES = """
# sample_module module example
- name: Test rolemapping
  castorsky.opensearch.opensearch_role_mapping:
    name: snapshot_management_read_access
    users:
      - tester
      - checker-user
    backend_roles: ["pepafsdv"]
    description: "Mapping new users to read access"
    state: present
    
- name: Display a hello message
  ansible.builtin.debug:
    msg: "{{ 'ansible-creator' | sample_module }}"
"""

__metaclass__ = type  # pylint: disable=C0103

from ansible_collections.castorsky.opensearch.plugins.module_utils.opensearch import OpenSearchModule


# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=12877, stdout_to_server=True, stderr_to_server=True)


def main() -> None:
    module_argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str', default=''),
        hosts=dict(type='list', default=[]),
        users=dict(type='list', default=[]),
        backend_roles=dict(type='list', default=[]),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
    )

    role_name = module.params['name']
    role_mapping_parameters = {
        'hosts': module.params['hosts'],
        'users': module.params['users'],
        'backend_roles': module.params['backend_roles'],
        'description': module.params['description'],
    }

    changed_flag = False
    module_result = None
    existent_role_mappings = module.os.security.get_role_mappings()

    if module.params['state'] == 'present':
        if role_name not in existent_role_mappings:
            module_result = module.os.security.create_role_mapping(
                role=role_name,
                body=role_mapping_parameters,
            )
            changed_flag = True
        else:
            role_mapping_differs = False
            for p in role_mapping_parameters:
                if role_mapping_parameters[p] != existent_role_mappings[role_name].get(p, ''):
                    role_mapping_differs = True
                    break
            if role_mapping_differs:
                module_result = module.os.security.patch_role_mappings(
                    body=[{
                        'op': 'replace',
                        'path': f'/{role_name}',
                        'value': role_mapping_parameters,
                    }]
                )
                changed_flag = True
    elif module.params['state'] == 'absent':
        if role_name in existent_role_mappings:
            module_result = module.os.security.delete_role_mapping(
                role=role_name,
            )
            changed_flag = True

    result = {'changed': changed_flag, 'content': module_result}
    module.exit_json(**result)


if __name__ == '__main__':
    main()
