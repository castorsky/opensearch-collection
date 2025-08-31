#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

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
      force:
        description:
          - Change password or hash to the specified on every run.
          - Has no effect if used with superadmin key/certificate.
        type: bool
        default: False
"""

EXAMPLES = """
# sample_module module example

- name: Display a hello message
  ansible.builtin.debug:
    msg: "{{ 'ansible-creator' | sample_module }}"
"""

__metaclass__ = type  # pylint: disable=C0103

from typing import TYPE_CHECKING

from ansible_collections.castorsky.opensearch.plugins.module_utils.opensearch import OpenSearchModule

import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=12877, stdout_to_server=True, stderr_to_server=True)

if TYPE_CHECKING:
    from typing import Callable


def main() -> None:
    module_argument_spec = dict(
        name=dict(type='str', required=True),
        description=dict(type='str', default=''),
        password=dict(type='str', no_log=True),
        password_hash=dict(type='str', no_log=True),
        force=dict(type='bool', default=False),
        opendistro_security_roles=dict(type='list', default=[]),
        backend_roles=dict(type='list', default=[]),
        attributes=dict(type='dict', default={}),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
        required_one_of=[('password', 'password_hash')],
    )

    user_name = module.params['name']
    user_parameters = {
        'opendistro_security_roles': module.params['opendistro_security_roles'],
        'backend_roles': module.params['backend_roles'],
        'attributes': module.params['attributes'],
    }

    changed_flag = False
    module_result = None
    existent_users = c.security.get_users()
    # if module.params['state'] == 'present':
    #     if role_name not in existent_roles:
    #         module_result = c.security.create_role(
    #             role=role_name,
    #             body=role_parameters,
    #         )
    #         changed_flag = True
    #     else:
    #         role_differs = False
    #         for p in role_parameters:
    #             if role_parameters[p] != existent_roles[role_name].get(p, ''):
    #                 role_differs = True
    #                 break
    #         if role_differs:
    #             module_result = c.security.patch_roles(
    #                 body=[{
    #                     'op': 'replace',
    #                     'path': f'/{role_name}',
    #                     'value': role_parameters,
    #                 }]
    #             )
    #             changed_flag = True
    # elif module.params['state'] == 'absent':
    #     if role_name in existent_roles:
    #         module_result = c.security.delete_role(
    #             role=role_name,
    #         )
    #         changed_flag = True

    result = {'changed': changed_flag, 'content': module_result}
    module.exit_json(**result)


if __name__ == '__main__':
    main()
