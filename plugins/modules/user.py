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
  - Manage existing Confluent Cloud users.
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
  description: Cluster metadata, including create timestamp and updated timestamp
  type: dict
  returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def cluster_remove(module, resource_id):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/cmk/v2/clusters",
        resource_key_id=resource_id
    )

    return(confluent.absent(data={ 'environment': module.params.get('environment') }))


def cluster_create(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/cmk/v2/clusters",
    )

    return(confluent.create({ 
            'spec':  {
                'display_name': module.params.get('name'),
                'availability': module.params.get('availability'),
                'cloud': module.params.get('cloud'),
                'region': module.params.get('region'),
                'config': {
                        'kind': module.params.get('kind'),
                        'cku': module.params.get('cku'),
                        'encryption_key': module.params.get('encryption_key'),
                    },
                'environment': {
                        'id': module.params.get('environment'),
                    },
                'network': {
                        'id': module.params.get('network'),
                    },
                },
        }))


def cluster_update(module, cluster):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/cmk/v2/clusters",
        resource_key_id=cluster['id']
    )

    return(confluent.update(cluster, {
            'spec':  {
                'display_name': module.params.get('name'),
                'config': {
                        'kind': module.params.get('kind'),
                        #'kind': 'Standard',
                        #'cku': module.params.get('cku'),
                        #'encryption_key': module.params.get('encryption_key'),
                    },
                },
    }, required = {
            'spec':  {
                'environment': {
                        'id': module.params.get('environment'),
                    },
                },
    }))


def get_clusters(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/cmk/v2/clusters",
    )

    resources = confluent.query(data={ 'environment': module.params.get('environment'), 'page_size': 100 })
    return(resources['data'])


def cluster_process(module):
    # Get existing cluster if it exists
    clusters = get_clusters(module)

    if clusters and module.params.get('id') and len([e for e in clusters if e['id'] in module.params.get('id')]):
        cluster = [e for e in clusters if e['id'] in module.params.get('id')][0]
    elif clusters and module.params.get('name') and len([e for e in clusters if e['spec']['display_name'] in module.params.get('name')]):
        cluster = [e for e in clusters if e['spec']['display_name'] in module.params.get('name')][0]
    else:
        cluster = None

    # Manage cluster removal
    if module.params.get('state') == 'absent' and not cluster:
        return({"changed": False})
    elif module.params.get('state') == 'absent' and cluster:
        return(cluster_remove(module, cluster['id']))

    # Create cluster
    elif module.params.get('state') == 'present' and not cluster:
        return(cluster_create(module))

    # Check for update
    else:
        return(cluster_update(module, cluster))


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['id'] = dict(type='str')
    argument_spec['name'] = dict(type='str')
    argument_spec['state'] = dict(default='present', choices=['present', 'absent'])
    argument_spec['environment'] = dict(type='str', required=True)
    argument_spec['availability'] = dict(default='SINGLE_ZONE', choices=['SINGLE_ZONE', 'MULTI_ZONE'])
    argument_spec['cloud'] = dict(type='str', choices=['AWS', 'GCP', 'AZURE'])
    argument_spec['region'] = dict(type='str')
    argument_spec['kind'] = dict(type='str', choices=['Basic', 'Standard', 'Dedicated'])
    argument_spec['cku'] = dict(type='int', default=1)
    argument_spec['network'] = dict(type='str')
    argument_spec['encryption_key'] = dict(type='str')

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=(("state", "present", ("name","environment","availability","cloud","region","kind",)),
                     ("kind", "Dedicated", ("cky","network",)),),
    )

    try:
        module.exit_json(**cluster_process(module))
    except Exception as e:
        module.fail_json(msg='failed to process cluster, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
