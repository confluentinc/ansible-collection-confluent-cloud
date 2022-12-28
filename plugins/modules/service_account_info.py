#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: service_account_info
short_description: Get information on existing service accounts
description:
  - Enumerate and filter service accounts within a Confluent Cloud environment.
  - Note this is different than user accounts which uses its own module.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  ids:
    description:
      - List of service accounts filtered by Id
      - Mutually exclusive when used with `names`.
    type: list
    elements: str
  names:
    description:
      - List of users filtered by name.
      - Mutually exclusive when used with `ids`.
    type: list
    elements: str
"""

EXAMPLES = """
- name: List all service accounts in the Confluent Cloud org
  confluent.cloud.service_account_info:
- name: List service accounts that match the given Ids
  confluent.cloud.service_account_info:
    ids:
      - sa-lz51vz
      - sa-logpdp
- name: List service accounts that match the given Names
  confluent.cloud.service_account_info:
    names:
      - application_1
"""

RETURN = """
---
service_accounts:
  description: Dictionary of matching users, keyed by user id
  returned: success
  type: dict
  contains:
    id:
      description: Service account id
      type: str
      returned: success
      sample: sa-lz51vz
    name:
      description: A human-readable name for the Service Account
      type: str
      returned: success
      sample: application_1
    description:
      description: A free-form description of the Service Account
      type: str
      returned: success
      sample: Service account for Application 1
    metadata:
      description: User metadata, including create timestamp and updated timestamp
      type: dict
      returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def get_service_accounts_info(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/service-accounts",
    )

    resources = confluent.query(data={'page_size': 100})

    if resources and module.params.get('ids'):
        service_accounts = [u for u in resources['data'] if u['id'] in module.params.get('ids')]
    elif resources and module.params.get('names'):
        service_accounts = [u for u in resources['data'] if u['display_name'] in module.params.get('names')]
    else:
        service_accounts = resources['data']

    return({'service_accounts': {s['id']: s for s in service_accounts}})


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
        module.exit_json(**get_service_accounts_info(module))
    except Exception as e:
        module.fail_json(msg='failed to get service_account info, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
