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
    params_differ,
)

# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=12877, stdout_to_server=True, stderr_to_server=True)

from typing import TYPE_CHECKING

from ansible.module_utils.basic import AnsibleModule  # type: ignore

if TYPE_CHECKING:
    from typing import Callable


def index_name_is_valid(name: str) -> bool:
    """
    Validate OpenSearch index name according to naming restrictions:
    - All letters must be lowercase
    - Cannot begin with underscores (_) or hyphens (-)
    - Cannot contain spaces, commas, or the following characters: :, ", *, +, /, \\, |, ?, #, >, or <
    """
    if name.startswith('_') or name.startswith('-'):
        return False

    forbidden_chars = [' ', ',', ':', '"', '*', '+', '/', '\\', '|', '?', '#', '>', '<']
    for char in forbidden_chars:
        if char in name:
            return False

    if name != name.lower():
        return False

    return True


def main() -> None:
    module_argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        settings=dict(type="dict", default={}),
        mappings=dict(type="dict", default={}),
        aliases=dict(type="dict", default={}),
        description=dict(type="str", default=""),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
        supports_check_mode=True,
        api_prefix="/",
    )

    index_name = module.params["name"]
    if not index_name_is_valid(index_name):
        module.fail_json(msg=f"Failed to validate index name: {index_name}")

    # Parameters that are used in OpenSearch API request body.
    index_parameters = {
        "settings": {"index": module.params["settings"]},
        "mappings": module.params["mappings"],
        "aliases": module.params["aliases"],
    }

    changed_flag = False
    module_result = None

    existent_index = module.opensearch_request(None, module.api_prefix + index_name, "GET")

    if module.params["state"] == "present":
        if not existent_index:
            if not module.check_mode:
                module.opensearch_request(
                    index_parameters, module.api_prefix + index_name, "PUT"
                )
            module_result = {"message": f"'{index_name}' was created.", "status": "CREATED"}
            changed_flag = True
        else:
            existing_settings = existent_index[index_name]["settings"]["index"]
            existing_mappings = existent_index[index_name]["mappings"]
            if params_differ(module.params["settings"], existing_settings):
                request_body = {"index": module.params["settings"]}
                if not module.check_mode:
                    module.opensearch_request(request_body, module.api_prefix + index_name + "/_settings", "PUT")
                changed_flag = True
                module_result = {"message": f"'{index_name}' was updated.", "status": "UPDATED"}
            if params_differ(module.params["mappings"], existing_mappings):
                request_body = module.params["mappings"]
                if not module.check_mode:
                    module.opensearch_request(request_body, module.api_prefix + index_name + "/_mapping", "PUT")
                changed_flag = True
                module_result = {"message": f"'{index_name}' was updated.", "status": "UPDATED"}
            if not changed_flag:
                module_result = {"message": f"'{index_name}' is up to date.", "status": "OK"}

            # if params_differ(module.params["aliases"], existent_index["aliases"]):
            #     request_body = module.params["mappings"]
            #     module.opensearch_request(request_body, module.api_prefix + index_name + "/_mapping", "PUT")

        # elif force_update or params_differ(index_parameters, existent_index):
        #     patch_body = [
        #         {
        #             "op": "replace",
        #             "path": "/" + index_name,
        #             "value": index_parameters,
        #         }
        #     ]
        #     if not module.check_mode:
        #         module.opensearch_request(None, module.api_prefix, "PATCH")
        #     module_result = {"message": f"'{index_name}' was updated.", "status": "UPDATED"}
        #     changed_flag = True
        # else:
        #     module_result = {"message": f"'{index_name}' is up to date.", "status": "OK"}
    elif module.params["state"] == "absent":
        if existent_index:
            if not module.check_mode:
                module.opensearch_request(None, module.api_prefix + index_name, "DELETE")
            module_result = {"message": f"'{index_name}' was deleted.", "status": "DELETED"}
            changed_flag = True
        else:
            module_result = {"message": f"'{index_name}' not found.", "status": "OK"}

    result = {"changed": changed_flag, "message": module_result}
    module.exit_json(**result)


if __name__ == "__main__":
    main()
