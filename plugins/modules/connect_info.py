#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: connect_info
short_description: Get information on existing connectors
description:
  - Enumerate and filter connectors within Confluent Cloud.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  environment:
    description:
      - The environment to which this belongs.
    type: str
    required: True
  cluster:
    description:
      - The cluster to which this belongs.
    type: str
    required: True
  names:
    description:
      - List of connector Names.
    type: list
    elements: str
  types:
    description:
      - List of connector types (sink or source).
    type: list
    elements: str
  connectors:
    description:
      - List of connector classes.
    type: list
    elements: str
"""

EXAMPLES = """
- name: List all available connectors
  confluent.cloud.connect_info:
    environment: env-f3a90de
    cluster: lkc-6wkr2
- name: List all sink connectors
  confluent.cloud.connect_info:
    environment: env-f3a90de
    cluster: lkc-6wkr2
    types:
      - sink
- name: List all Datagen connectors
  confluent.cloud.connect_info:
    environment: env-f3a90de
    cluster: lkc-6wkr2
    connectors:
      - DatagenSource
"""

RETURN = """
---
connectors:
  description: Dictionary of matching connectors, keyed by connector name
  returned: success
  type: dict
  contains:
    name:
      description: Connector name
      type: str
      returned: success
    config:
      description: Dict showing the connector's configuration parameters.  These vary by connector class
      type: str
      returned: success
    status:
      description: Dict showing the status of the connector
      type: str
      returned: success
    tasks:
      description: Dict showing the status of each connector task
      type: str
      returned: success
    type:
      description: Connector type (either source or sink)
      type: str
      returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def canonical_resource(resource):
    del(resource['id'])
    resource['name'] = resource['info']['name']
    del(resource['info']['name'])
    resource['type'] = resource['info']['type']
    del(resource['info']['type'])
    resource['config'] = resource['info']['config']
    del(resource['info']['config'])
    resource['tasks'] = resource['status']['tasks']
    del(resource['info'])
    resource['status'] = resource['status']['connector']
    return(resource)


def get_connectors_info(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/connect/v1/environments/%s/clusters/%s/connectors" % (
            module.params.get('environment'),
            module.params.get('cluster'),
        )
    )

    resources = confluent.query(data={'expand': 'status,info', 'page_size': 100})

    if module.params.get('names'):
        connectors = [c for c in resources.values() if c['info']['name'] in module.params.get('names')]
    elif module.params.get('types'):
        connectors = [c for c in resources.values() if c['info']['type'] in module.params.get('types')]
    elif module.params.get('connectors'):
        connectors = [c for c in resources.values() if c['info']['config']['connector.class'] in module.params.get('connectors')]
    else:
        connectors = resources.values()

    return({'connectors': {c['info']['name']: canonical_resource(c) for c in connectors}})


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['environment'] = dict(type='str', required=True)
    argument_spec['cluster'] = dict(type='str', required=True)
    argument_spec['names'] = dict(type='list', elements='str')
    argument_spec['types'] = dict(type='list', elements='str')
    argument_spec['connectors'] = dict(type='list', elements='str')

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(**get_connectors_info(module))
    except Exception as e:
        module.fail_json(msg='failed to get connect info, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
