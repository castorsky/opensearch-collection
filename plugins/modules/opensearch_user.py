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
      password:
        description:
          - Password to set for this user on creation or update.
          - The Security plugin hashes the password beofre storing it.
          - Password can be updated in two cases: when any of other options was change or when O(force=true).
          - O(password) and O(password_hash) are mutually exclusive.
        type: str
      password_hash:
        description:
          - Hashed user password to set for this user on creation or update.
          - Password can be updated in two cases: when any of other options was change or when O(force=true).
          - O(password_hash) and O(password) are mutually exclusive.
        type: str
      force:
        description:
          - Replace password or hash with the specified value. All other attributes will be replaced too.
          - Password will not be updated when O(force=false) and other attributes have not changed.
        type: bool
        default: False
"""

EXAMPLES = """
# sample_module module example
- name: Create OpenSearch user
  castorsky.opensearch.opensearch_user:
    name: "checker-user"
    password: "#v3DWeSVDtD2~eqm1"
    description: "Checker User"
    opendistro_security_roles:
      - all_access
    attributes:
      shell: "/bin/tcsh"
      home: "/home/checker"
    state: present
    
- name: Display a hello message
  ansible.builtin.debug:
    msg: "{{ 'ansible-creator' | sample_module }}"
"""

__metaclass__ = type  # pylint: disable=C0103

from ansible_collections.castorsky.opensearch.plugins.module_utils.opensearch import (
    OpenSearchModule,
)


def main() -> None:
    module_argument_spec = dict(
        name=dict(type="str", required=True),
        password=dict(type="str", no_log=True),
        password_hash=dict(type="str", no_log=True),
        force=dict(type="bool", default=False),
        opendistro_security_roles=dict(type="list", default=[]),
        backend_roles=dict(type="list", default=[]),
        attributes=dict(type="dict", default={}),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        description=dict(type="str", default=""),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
        supports_check_mode=True,
        required_one_of=[("password", "password_hash")],
        api_prefix="/_plugins/_security/api/internalusers/",
    )

    keys_to_skip = ["password", "password_hash"]

    # Parameters that are used in OpenSearch API request body.
    user_parameters = {
        "opendistro_security_roles": module.params["opendistro_security_roles"],
        "backend_roles": module.params["backend_roles"],
        "attributes": module.params["attributes"],
        "description": module.params["description"],
    }
    if module.params["password"]:
        user_parameters["password"] = module.params["password"]
    elif module.params["password_hash"]:
        user_parameters["password_hash"] = module.params["password_hash"]

    changed_flag, module_result = module.security_crud_sequence(user_parameters)

    result = {"changed": changed_flag, "message": module_result}
    module.exit_json(**result)


if __name__ == "__main__":
    main()
