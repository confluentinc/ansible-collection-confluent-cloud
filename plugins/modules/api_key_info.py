#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: api_key_info
short_description: Get information on existing API keys accounts
description:
  - Enumerate and filter API keys within a Confluent Cloud environment.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  ids:
    description:
      - List of API keys filtered by Id
      - Mutually exclusive when used with `names` or `owners`.
    type: list
    elements: str
  owners:
    description:
      - The owner to which this API key belows
      - Mutually exclusive when used with `names` or `ids`.
    type: list
    elements: str
  names:
    description:
      - List of API keys filtered by name.
      - Mutually exclusive when used with `ids` or `owners`.
    type: list
    elements: str
"""

EXAMPLES = """
- name: List all API keys in the Confluent Cloud org
  confluent.cloud.api_keys_info:
- name: List API keys that match the given Ids
  confluent.cloud.api_keys_info:
    ids:
      - YU6F4EODE4OXXYD4
      - FL2Z7WMXO5KJOPZY
- name: List API keys that match the given Names
  confluent.cloud.api_keys_info:
    names:
      - application_1
- name: List API keys that match the given Owner
  confluent.cloud.api_keys_info:
    owners:
      - u-lgyjxv
      - u-ld9ok7
"""

RETURN = """
---
api_keys:
  description: Dictionary of matching API keys, keyed by API key id
  returned: success
  type: dict
  contains:
    id:
      description: API key id
      type: str
      returned: success
      sample: AX6SWFVF46SLIK2P
    name:
      description: A human-readable name for the API key
      type: str
      returned: success
      sample: api_key_1
    description:
      description: A free-form description of the API key
      type: str
      returned: success
      sample: API Key 1
    owner:
      description: API key owner
      type: dict
      returned: success
      contains:
        id:
          description: Id for the owner
          type: str
          returned: success
          sample: u-lgyjxv
        kind:
          description: Kind of owner
          type: str
          returned: success
          sample: User
    metadata:
      description: User metadata, including create timestamp and updated timestamp
      type: dict
      returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def get_api_keys_info(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/api-keys",
    )

    resources = confluent.query(data={'page_size': 100})

    # Filter keys
    if resources and module.params.get('ids'):
        api_keys_raw = [a for a in resources['data'] if a['id'] in module.params.get('ids')]
    elif resources and module.params.get('owner'):
        api_keys_raw = [a for a in resources['data'] if a['spec']['owner']['id'] in module.params.get('owner')]
    elif resources and module.params.get('names'):
        api_keys_raw = [a for a in resources['data'] if a['spec']['display_name'] in module.params.get('names')]
    else:
        api_keys_raw = resources['data']

    # Transform key data
    api_keys = []
    for a in api_keys_raw:
        a['name'] = a['spec']['display_name']
        a.update({k: a['spec'][k] for k in a['spec'].keys() if k in ('description', 'owner', 'secret')})
        del(a['spec'])
        api_keys.append(a)

    return({'api_keys': {a['id']: a for a in api_keys}})


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['ids'] = dict(type='list', elements='str')
    argument_spec['owners'] = dict(type='list', elements='str')
    argument_spec['names'] = dict(type='list', elements='str')

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('ids', 'owners', 'names')
        ]
    )

    try:
        module.exit_json(**get_api_keys_info(module))
    except Exception as e:
        module.fail_json(msg='failed to get service_account info, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
