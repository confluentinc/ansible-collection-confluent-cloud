#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: user_info
short_description: Get information on existing users
description:
  - Enumerate and filter users within a Confluent Cloud environment.
  - Includes named users already setup and those who are invited by not yet activate.
  - Note this is different than service accounts which uses its own module.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  emails:
    description:
      - List of users filtered by email.
      - Mutually exclusive when used with `ids` or `names`.
    type: list
    elements: str
  names:
    description:
      - List of users filtered by full name.
      - Mutually exclusive when used with `ids` or `emails`.
    type: list
    elements: str
  ids:
    description:
      - List of users filtered by full name.
      - Mutually exclusive when used with `names` or `emails`.
    type: list
    elements: str
"""

EXAMPLES = """
- name: List all users in the Confluent Cloud org
  confluent.cloud.user_info:
- name: List users that match the given Ids
  confluent.cloud.user_info:
    ids:
      - u-l6xn83
      - u-ld9ok7
- name: List users that match the given Names
  confluent.cloud.user_info:
    names:
      - John Smith
- name: List users that match the given Emails
  confluent.cloud.user_info:
    names:
      - john@example.com
      - john.smith@example.com
"""

RETURN = """
---
users:
  description: Dictionary of matching users, keyed by user id
  returned: success
  type: dict
  contains:
    id:
      description: User id
      type: str
      returned: success
      sample: u-j31z28
    email:
      description: The user's email address
      type: str
      returned: success
      sample: john.smith@example.com
    full_name:
      description: The user's full name
      type: str
      returned: success
      sample: John Smith
    metadata:
      description: User metadata, including create timestamp and updated timestamp
      type: dict
      returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def get_users_info(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/users",
    )
    users_resources = confluent.query(data={'page_size': 100})
    resources = []
    if 'data' in users_resources:
        resources = users_resources['data']

    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/invitations",
    )
    invitations_resources = confluent.query(data={'page_size': 100})
    if 'data' in invitations_resources:
        for user in invitations_resources['data']:
            user['full_name'] = None
            user['invitation'] = user['id']
            user['id'] = user['user']['id']
            resources.append(user)

    if resources and module.params.get('ids'):
        users = [u for u in resources if u['id'] in module.params.get('ids')]
    elif resources and module.params.get('emails'):
        users = [u for u in resources if u['email'] in module.params.get('emails')]
    elif resources and module.params.get('names'):
        users = [u for u in resources if u['full_name'] in module.params.get('names')]
    else:
        users = resources

    return({'users': {u['id']: u for u in users}})


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['ids'] = dict(type='list', elements='str')
    argument_spec['emails'] = dict(type='list', elements='str')
    argument_spec['names'] = dict(type='list', elements='str')

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ('ids', 'names', 'emails')
        ]
    )

    try:
        module.exit_json(**get_users_info(module))
    except Exception as e:
        module.fail_json(msg='failed to get user info, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
