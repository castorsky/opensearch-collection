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
        state=dict(type="str", choices=["present", "absent"], default="present"),
        description=dict(type="str", default=""),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
    )
    api_prefix = "/_plugins/_security/api/tenants/"

    tenant_name = module.params["name"]
    tenant_parameters = {
        "description": module.params["description"],
    }
    changed_flag = False
    module_result = None
    existent_tenants = module.opensearch_request(None, api_prefix, "GET")
    existent_tenant = existent_tenants.get(tenant_name, None)

    if module.params["state"] == "present":
        if not existent_tenant:
            module_result = module.opensearch_request(
                tenant_parameters,
                api_prefix + tenant_name,
                "PUT",
            )
            changed_flag = True
        elif params_differ(tenant_parameters, existent_tenant):
            patch_body = [
                {
                    "op": "replace",
                    "path": "/" + tenant_name,
                    "value": tenant_parameters,
                }
            ]
            module_result = module.opensearch_request(
                patch_body,
                api_prefix,
                "PATCH",
            )
            changed_flag = True
        else:
            module_result = {
                "message": "Tenant is up to date.",
                "status": "OK",
            }
    elif module.params["state"] == "absent":
        if existent_tenant:
            module_result = module.opensearch_request(None, api_prefix + tenant_name, "DELETE")
            changed_flag = True
        else:
            module_result = {
                "message": "Tenant not found, nothing to delete.",
                "status": "OK",
            }

    result = {"changed": changed_flag, "content": module_result}
    module.exit_json(**result)


if __name__ == "__main__":
    main()
