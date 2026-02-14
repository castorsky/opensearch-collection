#!/usr/bin/python
# pylint: disable=E0401
# opensearch_index.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function


DOCUMENTATION = """
    module: opensearch_index
    author: Your Name (@username)
    version_added: "1.0.0"
    short_description: A custom module plugin for Ansible.
    description:
      - This is a demo module plugin designed to return Hello message.
    options:
      name:
        description: Value specified here is appended to the Hello message.
        type: str
        required: true
"""

EXAMPLES = """
- name: Run the module
  register: result
  opensearch_index:
    name: "ansible-creator"

- name: Display the message
  ansible.builtin.debug:
    msg: result.message
"""

RETURN = """
message:
  description:
  - A demo message.
  type: str
  returned: always
  sample: "Hello, ansible-creator"
"""


__metaclass__ = type  # pylint: disable=C0103

from ansible_collections.castorsky.opensearch.plugins.module_utils.opensearch import (
    OpenSearchModule,
)


from typing import TYPE_CHECKING

from ansible.module_utils.basic import AnsibleModule  # type: ignore


if TYPE_CHECKING:
    from typing import Callable


def main() -> None:
    module_argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        description=dict(type="str", default=""),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
        supports_check_mode=True,
        api_prefix="/_plugins/_security/api/roles/",
    )

    # Parameters that are used in OpenSearch API request body.
    index_parameters = {
        "description": module.params["description"],
    }

    changed_flag, module_result = module.security_crud_sequence(index_parameters)

    result = {"changed": changed_flag, "message": module_result}
    module.exit_json(**result)


if __name__ == "__main__":
    main()
