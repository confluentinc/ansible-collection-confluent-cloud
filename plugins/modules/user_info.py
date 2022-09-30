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
TODO
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
  description: TODO Dictionary of matching users, keyed by user id
  returned: success
  type: dict
  contains:
    id:
      description: Cluster id
      type: str
      returned: success
      sample: lkc-7yxkd2
    metadata:
      description: Cluster metadata, including create timestamp and updated timestamp
      type: dict
      returned: success
    spec:
      description: Cluster spec
      type: dict
      returned: success
      contains:
        display_name:
          description: The name of the user
          type: str
          returned: success
        api_endpoint:
          description: API endpoint
          type: str
          returned: success
          sample: https://pkac-4nd3z.us-west4.gcp.confluent.cloud
        http_endpoint:
          description: The user HTTP request UR
          type: str
          returned: success
          sample: https://pkc-lzvrd.us-west4.gcp.confluent.cloud:443
        kafka_bootstrap_endpoint:
          description: The bootstrap endpoint used by Kafka clients to connect to the user
          type: str
          returned: success
          sample: SASL_SSL://pkc-lzvrd.us-west4.gcp.confluent.cloud:9092
        availability:
          description: The availability zone configuration of the user
          type: str
          returned: success
          sample: SINGLE_ZONE
        cloud:
          description: The cloud service provider in which the user is running (AWS, GCP, AZURE)
          type: str
          returned: success
          sample: AWS
        region:
          description: The cloud service provider region where the user is running
          type: str
          returned: success
          sample: us-west4
        config:
          description: The configuration of the Kafka user.
          type: dict
          returned: success
          contains:
            kind:
              description: The configuration of the Kafka user.
              type: str
              returned: success
              sample: Basic
        environment:
          description: The environment to which this belongs
          type: dict
          returned: success
          contains:
            id:
              description: Id of the referred resource
              type: str
              returned: success
              sample: env-12m16j
        network:
          description: The network associated with this object
          type: dict
          returned: success
          contains:
            id:
              description: Id of the referred resource
              type: str
              returned: success
            environment:
              description: Environment of the referred resource, if env-scoped
              type: str
              returned: success
        status:
          description: The status of the user
          type: dict
          returned: success
          contains:
            phase:
              description: The lifecyle phase of the user: PROVISIONED: user is provisioned; PROVISIONING: user provisioning is in progress; FAILED: provisioning failed
              type: str
              returned: success
              sample: PROVISIONED
            cku:
              description: The number of Confluent Kafka Units (CKUs) the Dedicated user currently has
              type: int
              returned: success
              sample: 1
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

    resources = confluent.query(data={ 'page_size': 100 })

    if resources and module.params.get('ids'):
        users = [u for u in resources['data'] if u['id'] in module.params.get('ids')]
    elif resources and module.params.get('emails'):
        users = [u for u in resources['data'] if u['email'] in module.params.get('emails')]
    elif resources and module.params.get('names'):
        users = [u for u in resources['data'] if u['full_name'] in module.params.get('names')]
    else:
        users = resources['data']

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
