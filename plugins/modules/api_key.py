#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: api_key
short_description: Manage existing Confluent Cloud API keys
description:
  - Manage existing Confluent Cloud API keys within a Confluent Cloud environment.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  id:
    description: API key Id
    type: str
  name:
    description:
      - API key name
      - Mutation after creation requires supplying the user id.
    type: str
  description:
      description: A free-form description of the API key
      type: str
  state:
    description:
      - If `absent`, the API key will be removed.
        Note that absent will not cause API key to fail if the API key does not exist.
    default: present
    choices:
      - absent
      - present
    type: str
  owner:
    description:
      - iam.v2.User or iam.v2.ServiceAccount ID that will own the API key.
      - API keys can only be created by the owner of the Confluent Cloud API keys used to authenticate this call.
      - Immutable after deployment.
    type: str
  resource:
    description:
      - cmk.v2.Cluster id (or null if not associated with a resource).
      - Immutable after deployment.
    type: str
"""

EXAMPLES = """
- name: Create new API key
  confluent.cloud.api_key:
    name: application_1_key
    owner: u-j31z28
    state: present
- name: Delete API key (by id)
  confluent.cloud.api_key:
    id: YU6F4EODE4OXXYD4
    state: absent
- name: Delete user (by name)
  confluent.cloud.api_key:
    name: application_1_key
    state: absent
"""

RETURN = """
---
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
secret:
  description:
    - The API key secret.
    - Only provided in create requests
  type: str
  returned: success
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
resource:
  description: cmk.v2.Cluster id (or null if not associated with a resource).
  type: dict
  returned: success
  contains:
    id:
      description: Id for the resource
      type: str
      returned: success
      sample: lkc-c29js0
    kind:
      description: Kind of resource
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


def api_key_remove(module, resource_id):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/api-keys",
        resource_key_id=resource_id
    )

    return(confluent.absent())


def api_key_update(module, api_key):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/api-keys",
        resource_key_id=api_key['id']
    )

    return(confluent.update(api_key, {
        'spec': {
            'display_name': module.params.get('name'),
            'description': module.params.get('description'),
        },
    }))


def api_key_create(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/api-keys",
    )

    request = confluent.create({
        'spec': {
            'display_name': module.params.get('name'),
            'description': module.params.get('description'),
            'owner': {
                'id': module.params.get('owner'),
            },
        },
    })
    if module.params.get('resource'):
        request['spec']['resource'] = {
            'id': module.params.get('resource'),
        }

    response = confluent.create(request)

    if 'spec' in response:
        response['name'] = response['spec']['display_name']
        response.update({k: response['spec'][k] for k in response['spec'].keys() if k in ('description', 'owner', 'resource', 'secret')})
        del(response['spec'])

    return(response)


def get_api_keys(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/api-keys",
    )

    resources = confluent.query(data={'page_size': 100})

    # Transform key data
    api_keys = []
    for a in resources['data']:
        a['name'] = a['spec']['display_name']
        a.update({k: a['spec'][k] for k in a['spec'].keys() if k in ('description', 'owner', 'resource', 'secret')})
        del(a['spec'])
        api_keys.append(a)

    return(api_keys)


def api_key_process(module):
    # Get existing api_key if it exists
    api_keys = get_api_keys(module)

    if module.params.get('id') and len([ak for ak in api_keys if ak['id'] == module.params.get('id')]):
        api_key = [ak for ak in api_keys if ak['id'] == module.params.get('id')][0]
    elif module.params.get('name') and len([u for u in api_keys if u['name'] == module.params.get('name')]):
        api_key = [ak for ak in api_keys if ak['name'] == module.params.get('name')][0]
    else:
        api_key = None

    # Manage api_key removal
    if module.params.get('state') == 'absent' and not api_key:
        return({"changed": False})
    elif module.params.get('state') == 'absent' and api_key:
        return(api_key_remove(module, api_key['id']))

    # Create api_key
    elif module.params.get('state') == 'present' and not api_key:
        return(api_key_create(module))

    # Check for update
    else:
        return(api_key_update(module, api_key))


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['id'] = dict(type='str')
    argument_spec['name'] = dict(type='str')
    argument_spec['description'] = dict(type='str')
    argument_spec['state'] = dict(default='present', choices=['present', 'absent'])
    argument_spec['owner'] = dict(type='str')
    argument_spec['resource'] = dict(type='str', default=None)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(**api_key_process(module))
    except Exception as e:
        module.fail_json(msg='failed to process api_key, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
