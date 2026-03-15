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
      settings:
        description:
          - Object with index settings to be applied.
          - Settings can be specified in a flat (V({"codec.qatmode": true})) or nested (V({"codec": {"qatmode": true}})) format.
          - Settings that are considered "static" (
            L(Static Index Settings,https://docs.opensearch.org/latest/install-and-configure/configuring-opensearch/index-settings/#static-index-level-index-settings)
            ) can be updated only when O(force=true) is specified. In this case index will be closed and opened back.
          - Parameter V(number_of_shards) cannot be updated after index was created and ignored even if O(force=true).
          - Static settings will not be updated and silently ignored if O(force=false).
          - Dynamic settings can be updated without closing the index and do not require O(force=true).
        type: dict
        default: {}
      force:
        description:
          - Force update of the index settings that can be changed only on a closed index.
          - Therefore, index will be closed and opened back if needed.
        type: bool
        default: false
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
    flatten_dict,
)

import pydevd_pycharm

pydevd_pycharm.settrace("localhost", port=43555, stdout_to_server=True, stderr_to_server=True)

# Settings that cannot be updated after index was created.
UNBREAKABLE_SETTINGS = ["number_of_shards"]

# Settings that can be updated only on a closed index.
STATIC_SETTINGS = [
    "number_of_routing_shards",
    "shard.check_on_startup",
    "codec",
    "codec.compression_level",
    "codec.qatmode",
    "routing_partition_size",
    "soft_deletes.retention_lease.period",
    "sort.field",
    "sort.order",
    "sort.mode",
    "sort.missing",
    "load_fixed_bitset_filters_eagerly",
    "hidden",
    "merge.policy",
    "merge_on_flush.enabled",
    "merge_on_flush.max_full_flush_merge_wait_time",
    "check_pending_flush.enabled",
    "use_compound_file",
    "append_only.enabled",
    "derived_source.enabled",
]

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
    if name.startswith("_") or name.startswith("-"):
        return False

    forbidden_chars = [" ", ",", ":", '"', "*", "+", "/", "\\", "|", "?", "#", ">", "<"]
    for char in forbidden_chars:
        if char in name:
            return False

    if name != name.lower():
        return False

    return True


def update_index_settings(module: OpenSearchModule, existing_index: dict) -> tuple[bool, list[str]]:
    """
    Find out which settings need to be updated. Apply changes if needed.
    Args:
        module: OpenSearch(Ansible) module used to get wanted config and perform requests to cluster.
        existing_index: Existing index information as returned by OpenSearch API.

    Returns:
        tuple of:
            - bool: True if any settings were changed, False otherwise.
            - list[str]: List of messages describing what settings were updated.
    """
    settings_changed = False
    settings_messages = []
    name = module.params["name"]

    wanted_settings = flatten_dict(module.params["settings"])
    existing_settings = flatten_dict(existing_index[name]["settings"]["index"])

    # Remove params that API cannot update.
    for key in UNBREAKABLE_SETTINGS:
        wanted_settings.pop(key, None)

    # Split settings into static and dynamic categories based on whether they can be modified without closing index.
    static_settings = {
        key: value for key, value in wanted_settings.items() if key in STATIC_SETTINGS
    }
    dynamic_settings = {
        key: value for key, value in wanted_settings.items() if key not in STATIC_SETTINGS
    }

    static_changed = params_differ(static_settings, existing_settings)
    dynamic_changed = params_differ(dynamic_settings, existing_settings)

    if static_changed and module.params["force"]:
        # Make changes both to static and dynamic parameters if "force" was set.
        if not module.check_mode:
            # Close index, apply changes and open index back.
            module.opensearch_request(None, module.api_prefix + name + "/_close", "POST")
            module.opensearch_request(
                wanted_settings, module.api_prefix + name + "/_settings", "PUT"
            )
            module.opensearch_request(None, module.api_prefix + name + "/_open", "POST")
        settings_changed = True
        if dynamic_changed:
            settings_messages.append("dynamic settings updated")
        settings_messages.append("static settings force-updated")

    elif static_changed and not dynamic_changed:
        # Static settings cannot be updated without force, so skip the update.
        settings_messages.append("static settings update skipped")

    elif dynamic_changed:
        # Ignore changes to static parameters even they are present because "force" was not set.
        # Update only parameters that can be changed dynamically.
        request_parameters = {"index": dynamic_settings}
        if not module.check_mode:
            module.opensearch_request(
                request_parameters, module.api_prefix + name + "/_settings", "PUT"
            )
        settings_changed = True
        if static_changed:
            settings_messages.append("static settings skipped")
        settings_messages.append("dynamic settings updated")

    return settings_changed, settings_messages


def update_index_mappings(module: OpenSearchModule, existing_index: dict) -> tuple[bool, list[str]]:
    """
    Find out which mappings need to be updated. Apply changes if needed.
    Args:
        module: OpenSearch(Ansible) module used to get wanted config and perform requests to cluster.
        existing_index: Existing index information as returned by OpenSearch API.

    Returns:
        tuple of:
            - bool: True if any mappings were changed, False otherwise.
            - list[str]: List of messages indicating what was changed.
    """
    mappings_messages = []
    name = module.params["name"]

    wanted_mappings = module.params["mappings"]
    existing_mappings = existing_index[name]["mappings"]

    mappings_changed = params_differ(wanted_mappings, existing_mappings)

    if mappings_changed:
        if not module.check_mode:
            module.opensearch_request(
                wanted_mappings, module.api_prefix + name + "/_mapping", "PUT"
            )
        mappings_messages.append("mappings updated")

    return mappings_changed, mappings_messages

def main() -> None:
    module_argument_spec = dict(
        name=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        settings=dict(type="dict", default={}),
        mappings=dict(type="dict", default={}),
        aliases=dict(type="dict", default={}),
        force=dict(type="bool", default=False),
    )

    module = OpenSearchModule(
        argument_spec=module_argument_spec,
        supports_check_mode=True,
        api_prefix="/",
    )

    index_name = module.params["name"]
    if not index_name_is_valid(index_name):
        module.fail_json(msg=f"Failed to validate index name: {index_name}")

    changed_flag = False
    module_result = None

    existent_index = module.opensearch_request(None, module.api_prefix + index_name, "GET")

    if module.params["state"] == "present":
        if not existent_index:
            if not module.check_mode:
                request_parameters = {
                    "settings": module.params["settings"],
                    "mappings": module.params["mappings"],
                    "aliases": module.params["aliases"],
                }
                module.opensearch_request(request_parameters, module.api_prefix + index_name, "PUT")
            module_result = {"message": f"'{index_name}' was created.", "status": "CREATED"}
            changed_flag = True
        else:
            result_messages = []

            settings_chgd, settings_msgs = update_index_settings(module, existent_index)
            changed_flag = changed_flag or settings_chgd
            result_messages.extend(settings_msgs)

            mappings_chgd, mappings_msgs = update_index_mappings(module, existent_index)
            changed_flag = changed_flag or mappings_chgd
            result_messages.extend(mappings_msgs)

            # existing_mappings = existent_index[index_name]["mappings"]
            # if params_differ(module.params["mappings"], existing_mappings):
            #     request_body = module.params["mappings"]
            #     if not module.check_mode:
            #         module.opensearch_request(request_body, module.api_prefix + index_name + "/_mapping", "PUT")
            #     changed_flag = True
            #     module_result = {"message": f"'{index_name}' was updated.", "status": "UPDATED"}

            if not changed_flag:
                msgs = ["is up to date"]
                msgs.extend(result_messages)
                module_result = {"message": f"'{index_name}' {', '.join(msgs)}.", "status": "OK"}
            else:
                module_result = {
                    "message": f"'{index_name}' was updated: {', '.join(result_messages)}.",
                    "status": "UPDATED",
                }

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
