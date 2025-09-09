#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

DOCUMENTATION = """
    module: opensearch_role_mapping
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


def main() -> None:
    module_argument_spec = dict(
        name=dict(type='str', required=True),
        hosts=dict(type='list', default=[]),
        users=dict(type='list', default=[]),
        backend_roles=dict(type='list', default=[]),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        description=dict(type='str', default=''),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
    )

    mandatory_params = ['hosts', 'users', 'backend_roles', 'description']
    module.default_sequence(api_group='security', object_type='role_mapping', object_params=mandatory_params)

    result = {'changed': module.changed, 'content': module.result}
    module.exit_json(**result)


if __name__ == '__main__':
    main()
