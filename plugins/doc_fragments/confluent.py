# Copyright: (c) 2022,
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):
    # Standard documentation
    DOCUMENTATION = r'''
    options:
        api_key:
          description: Confluent Cloud API Key
          type: str
          required: true
        api_secret:
          description: Confluent Cloud API Secret
          type: str
          required: true
        api_timeout:
          description: Timeout used for the API requests.
          type: int
          default: 60
        api_retries:
          description: Amount of max retries for the API requests.
          type: int
          default: 5
        api_retry_max_delay:
          description: Exponential backoff delay in seconds between retries up to this max delay value.
          type: int
          default: 12
        api_endpoint:
          description: Endpoint used for the API requests.
          type: str
          default: https://api.confluent.cloud
        validate_certs:
          description: Whether to vaidate API endpoint TLS certs
          type: bool
          default: True
    '''
