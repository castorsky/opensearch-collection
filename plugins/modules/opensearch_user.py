#!/usr/bin/python
# pylint: disable=E0401
# sample_module.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

from typing import Any

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
    params_differ,
)

# import pydevd_pycharm
#
# pydevd_pycharm.settrace("localhost", port=43555, stdout_to_server=True, stderr_to_server=True)


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
        required_one_of=[("password", "password_hash")],
    )
    api_prefix = "/_plugins/_security/api/internalusers/"

    user_name = module.params["name"]
    user_parameters = {
        "opendistro_security_roles": module.params["opendistro_security_roles"],
        "backend_roles": module.params["backend_roles"],
        "attributes": module.params["attributes"],
        "description": module.params["description"],
    }
    user_parameters_with_pwd = user_parameters.copy()
    if module.params["password"]:
        user_parameters_with_pwd["password"] = module.params["password"]
    elif module.params["password_hash"]:
        user_parameters_with_pwd["password_hash"] = module.params["password_hash"]

    changed_flag = False
    module_result = None
    force_update = module.params["force"]
    existent_users = module.opensearch_request(None, api_prefix, "GET")
    existent_user = existent_users.get(user_name, None)

    if module.params["state"] == "present":
        if not existent_user:
            module_result = module.opensearch_request(
                user_parameters_with_pwd,
                api_prefix + user_name,
                "PUT",
            )
            changed_flag = True
        elif force_update or params_differ(user_parameters, existent_user):
            patch_body = [
                {
                    "op": "replace",
                    "path": "/" + user_name,
                    "value": user_parameters_with_pwd,
                }
            ]
            module_result = module.opensearch_request(patch_body, api_prefix, "PATCH")
            module_result["message"] = f"'{user_name}' {module_result['message']}"
            changed_flag = True
        else:
            module_result = {
                "message": f"'{user_name}' user is up to date.",
                "status": "OK",
            }
    elif module.params["state"] == "absent":
        if existent_user:
            module_result = module.opensearch_request(None, api_prefix + user_name, "DELETE")
            changed_flag = True
        else:
            module_result = {
                "message": f"'{user_name}' user not found, nothing to delete.",
                "status": "OK",
            }

    result = {"changed": changed_flag, "content": module_result}
    module.exit_json(**result)


if __name__ == "__main__":
    main()
