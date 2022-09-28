#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: environment_info
short_description: Get information on existing environments
description:
  - Enumerate and filter environments within Confluent Cloud.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  names:
    description:
      - List of environment Names.
      - Mutually exclusive when used with `ids`
    type: list
    elements: str
  ids:
    description:
      - List of environment Ids.
      - Mutually exclusive when used with `names`
    type: list
    elements: str
"""

EXAMPLES = """
- name: List all available environments
  confluent.cloud.environment_info:
- name: List environments that match the given Ids
  confluent.cloud.environment_info:
    ids:
      - env-f3a90de
      - env-3887de0
- name: List environments that match the given Names
  confluent.cloud.environment_info:
    names:
      - Test
      - Production
"""

RETURN = """
---
environments:
  description: Dictionary of matching envrionments, keyed by environment id
  returned: success
  type: dict
  contains:
    display_name:
      description: Environment name
      type: str
      returned: success
    id:
      description: Environment id
      type: str
      returned: success
      sample: env-9v5v5
    metadata:
      description: Environment metadata, including create timestamp and updated timestamp
      type: dict
      returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def get_environments_info(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/org/v2/environments",
    )

    resources = confluent.query(data={ 'page_size': 100 })

    if module.params.get('ids'):
        environments = [e for e in resources['data'] if e['id'] in module.params.get('ids')]
    elif module.params.get('names'):
        environments = [e for e in resources['data'] if e['display_name'] in module.params.get('names')]
    else:
        environments = resources['data']

    return({'environments': {e['id']: e for e in environments}})


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['ids'] = dict(type='list', elements='str')
    argument_spec['names'] = dict(type='list', elements='str')

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('ids', 'names')
        ]
    )

    try:
        module.exit_json(**get_environments_info(module))
    except Exception as e:
        module.fail_json(msg='failed to get environment info, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
