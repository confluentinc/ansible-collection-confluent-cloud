#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: user
short_description: Manage existing Confluent Cloud users
description:
  - Manage existing Confluent Cloud users within a Confluent Cloud environment.
  - Includes named users already setup and those who are invited by not yet activate.
  - Note this is different than service accounts which uses its own module.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  id:
    description: User Id
    type: str
  name:
    description: 
      - User's full name
      - Mutation after creation requires supplying the user id.
      - Mutation requires authentication with Cloud API keys owned this the user being changed
    type: str
  state:
    description:
      - If `absent`, the user will be removed.
        Note that absent will not cause User to fail if the User does not exist.
      - If `present`, the user will be invited.
    default: present
    choices:
      - absent
      - present
    type: str
  email:
    description: 
      - The user's email address.
      - Immutable after deployment.
    type: str
    required: True
"""

EXAMPLES = """
- name: Update existing user name
  confluent.cloud.user:
    name: John Smith
    id: u-j31z28
    state: present
- name: Delete user (by id)
  confluent.cloud.cluster_info:
  confluent.cloud.user:
    id: u-j31z28
    state: absent
- name: Delete user (by email)
  confluent.cloud.cluster_info:
  confluent.cloud.user:
    email: john.smith@example.com
    state: absent
"""

RETURN = """
---
id:
  description: User id
  type: str
  returned: success
  sample: u-j31z28
email:
  description: User email
  type: str
  returned: success
  sample: john.smith@example.com
name:
  description: User full name
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


def user_remove(module, user):
    if user['kind'] == 'Invitation':  
        resource_id = user['invitation']
        resource_path = "/iam/v2/invitations"
    else:  
        resource_id = user['id']
        resource_path = "/iam/v2/users"

    confluent = AnsibleConfluent(
        module=module,
        resource_path=resource_path,
        resource_key_id=resource_id
    )

    return(confluent.absent())


def user_update(module, user):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/users",
        resource_key_id=user['id']
    )

    return(confluent.update(user, {
            'full_name': module.params.get('name'),
    }))


def user_create(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/invitations",
    )

    response = confluent.create({
            'email': module.params.get('email'),
        })

    if 'user' in response:
        response['full_name'] = None
        response['invitation'] = response['id']
        response['id'] = response['user']['id']

    return(response)

def get_users(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/users",
    )
    users_resources = confluent.query(data={ 'page_size': 100 })
    resources = []
    if 'data' in users_resources:
        resources = users_resources['data']

    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/invitations",
    )
    invitations_resources = confluent.query(data={ 'page_size': 100 })
    if 'data' in invitations_resources:
        for user in invitations_resources['data']:
            user['full_name'] = None
            user['invitation'] = user['id']
            user['id'] = user['user']['id']
            resources.append(user)

    return(resources)


def user_process(module):
    # Get existing user if it exists
    users = get_users(module)

    if module.params.get('id') and len([u for u in users if u['id']==module.params.get('id')]):
        user = [u for u in users if u['id']==module.params.get('id')][0]
    elif module.params.get('email') and len([u for u in users if u['email']==module.params.get('email')]):
        user = [u for u in users if u['email']==module.params.get('email')][0]
    else:
        user = None

    # Manage user removal
    if module.params.get('state') == 'absent' and not user:
        return({"changed": False})
    elif module.params.get('state') == 'absent' and user:
        return(user_remove(module, user))

    # Create user
    elif module.params.get('state') == 'present' and not user:
        return(user_create(module))

    # Check for update
    else:
        return(user_update(module, user))


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['id'] = dict(type='str')
    argument_spec['name'] = dict(type='str')
    argument_spec['email'] = dict(type='str')
    argument_spec['state'] = dict(default='present', choices=['present', 'absent'])

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(**user_process(module))
    except Exception as e:
        module.fail_json(msg='failed to process user, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
