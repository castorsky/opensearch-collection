#!/usr/bin/python
# pylint: disable=E0401
# opensearch.py - A custom connection plugin for Ansible.
# Author: Your Name (@username)
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, annotations, division, print_function

# import pydevd_pycharm
# pydevd_pycharm.settrace('localhost', port=12877, stdout_to_server=True, stderr_to_server=True)

DOCUMENTATION = """
    name: opensearch_http
    author: Castor Sky (@castorsky)
    version_added: "0.1.0"
    short_description: Maintain persistent connection to an OpenSearch server
    description:
      - Use the V(opensearch_py) library to connect to an OpenSearch server.
      - Maintain persistent connection to an OpenSearch server to make series of commands execute faster.
    options:
      api_host:
        description:
          - Name of the OpenSearch host.
        required: true
        type: string
        default: inventory_hostname
        vars:
          - name: ansible_host
          - name: inventory_hostname
          - name: ansible_api_host
        env:
          - name: OPENSEARCH_API_HOST
      api_port:
        description:
          - API port on the OpenSearch host.
        type: int
        default: 9092
        vars:
          - name: ansible_opensearch_api_port
        env:
          - name: OPENSEARCH_API_PORT
      api_username:
        description:
          - Username to authenticate when connecting to the OpenSearch host.
        type: string
        vars:
          - name: 
        env:
          - name: OPENSEARCH_API_USERNAME
      api_password:
        description:
          - Password to authenticate when connecting to the OpenSearch host.
          - Some security related API endpoints are not available with password.
          - Use O(api_client_cert) instead of password to access those endpoints.
        type: string
        vars:
          - name: ansible_opensearch_api_password
        env:
          - name: OPENSEARCH_API_PASSWORD
      api_use_ssl:
        description:
          - Use plain HTTP or secured HTTPS when connecting to the OpenSearch host.
        default: true
        type: bool
        vars:
          - name: ansible_opensearch_api_use_ssl
        env:
          - name: OPENSEARCH_API_USE_SSL
      api_verify_certs:
        description:
          - Whether to verify server TLS certificates for validity.
        type: bool
        default: true
        vars:
          - name: ansible_opensearch_api_verify_certs
        env:
          - name: OPENSEARCH_API_VERIFY_CERTS
      api_ca_certs:
        description:
          - Path to the file with CA bundle.
        type: string
        vars:
          - name: ansible_opensearch_api_ca_certs
        env:
          - name: OPENSEARCH_API_CA_CERTS
      api_client_cert:
        description:
          - Path to the file with client certificate to authenticate in the OpenSearch API.
          - Could contain either single certificate or both certificate and private key.
        vars:
          - name: ansible_opensearch_api_client_cert
        env:
          - name: OPENSEARCH_API_CLIENT_CERT
      api_client_key:
        description:
          - Path to the file with client private key to authenticate in the OpenSearch API.
          - This parameter is used only when O(api_client_cert) contains only certificate.
        vars:
          - name: ansible_opensearch_api_client_key
        env:
          - name: OPENSEARCH_API_CLIENT_KEY
      persistent_command_timeout:
        description:
          - Timeout in seconds to wait response from the OpenSearch API.
        type: int
        default: 10
        vars:
          - name: ansible_opensearch_api_timeout
        env:
          - name: OPENSEARCH_API_TIMEOUT
"""

EXAMPLES = """
# sample_module module example

- name: Display a hello message
  ansible.builtin.debug:
    msg: "{{ 'ansible-creator' | sample_module }}"
"""

__metaclass__ = type  # pylint: disable=C0103

import traceback

# from ansible_collections.ansible.utils.plugins.plugin_utils.connection_base import (
#     PersistentConnectionBase,
# )
from ansible_collections.ansible.netcommon.plugins.plugin_utils.connection_base import (
    NetworkConnectionBase,
)

from ansible.errors import AnsibleError, AnsibleConnectionFailure
from ansible.utils.display import Display

OPENSEARCH_IMPORT_FAIL = None
try:
    from opensearchpy import OpenSearch, OpenSearchException

    OPENSEARCH_MODULE_OK = True
except ImportError:
    OPENSEARCH_MODULE_OK = False
    OPENSEARCH_IMPORT_FAIL = traceback.format_exc()

display = Display()


class Connection(NetworkConnectionBase):
    transport = "castorsky.opensearch.opensearch_http"
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        self._client = None

        self.api_host = self.get_option('api_host') or self._play_context.remote_addr
        self.api_port = self.get_option('api_port')
        self.api_username = self.get_option('api_username') or self._play_context.remote_user
        self.api_password = self.get_option('api_password')
        self.api_use_ssl = self.get_option('api_use_ssl')
        self.api_verify_certs = self.get_option('api_verify_certs')
        self.api_timeout = self.get_option('persistent_command_timeout')
        self.api_ca_certs = self.get_option('api_ca_certs')
        self.api_client_key = self.get_option('api_client_key')
        self.api_client_cert = self.get_option('api_client_cert')

    def _connect(self) -> Connection | None:
        if not OPENSEARCH_MODULE_OK:
            raise AnsibleConnectionFailure(
                "Could not load 'opensearch-py' library. Caught exception: %s" % OPENSEARCH_IMPORT_FAIL
            )
        super(Connection, self)._connect()

        if not self.connected:
            display.vvv(f"Connecting to OpenSearch at {self.api_host}:{self.api_host}", host=self.api_host)
            connection_params = {
                'hosts': [{'host': self.api_host, 'port': self.api_port}],
                'use_ssl': self.api_use_ssl,
                'timeout': self.api_timeout,
                'verify_certs': self.api_verify_certs,
            }

            if self.api_client_key and self.api_client_cert:
                connection_params.update({
                    'client_cert': self.api_client_cert,
                    'client_key': self.api_client_key,
                })
            else:
                connection_params.update({
                    'http_auth': (
                        self.api_username,
                        self.api_password,
                    ),
                })

            self._client = OpenSearch()
            self._connected = True

            return self

    @property
    def client(self) -> OpenSearch:
        """Return client object"""
        return self._client

    @property
    def connected(self):
        """Check if connection is established"""
        return self._connected
