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
)


def main() -> None:
    module_argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        description=dict(type="str", default=""),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
        supports_check_mode=True,
        api_prefix="/_plugins/_security/api/tenants/",
    )

    # Parameters that are used in OpenSearch API request body.
    tenant_parameters = {
        "description": module.params["description"],
    }

    changed_flag, module_result = module.security_crud_sequence(tenant_parameters)

    result = {"changed": changed_flag, "content": module_result}
    module.exit_json(**result)


if __name__ == "__main__":
    main()
