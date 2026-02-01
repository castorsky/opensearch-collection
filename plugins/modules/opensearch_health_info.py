#!/usr/bin/python
# pylint: disable=E0401
# opensearch_health_info.py - A custom module plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function


DOCUMENTATION = """
    module: opensearch_health_info
    author: Castor Sky (@castorsky)
    version_added: "0.1.0"
    short_description: Retrieve information about cluster health.
    description:
      - The module makes a request to health endpoint and returns response from cluster.
"""

EXAMPLES = """
- name: Run the module
  register: result
  opensearch_health_info:

- name: Display the message
  ansible.builtin.debug:
    msg: result.health
"""

RETURN = """
health:
  description:
  - Information about cluster with health status.
  type: dict
  returned: success
  sample: { "status": "green", "cluster_name": "docker-cluster", "unassigned_shards": 0, "number_of_nodes": 1 }
"""


__metaclass__ = type  # pylint: disable=C0103

from typing import TYPE_CHECKING

from ansible_collections.castorsky.opensearch.plugins.module_utils.opensearch import OpenSearchModule

if TYPE_CHECKING:
    from typing import Callable

def main() -> None:
    """Entry point for module execution"""

    module = OpenSearchModule(argument_spec={}, supports_check_mode=True)

    response = module.opensearch_request(None, '/_cluster/health', 'GET')
    health = response
    result = {
        "changed": False,
        "health": health,
    }
    module.exit_json(**result)

if __name__ == "__main__":
    main()
