#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: cluster_info
short_description: Get information on existing clusters
description:
  - Enumerate and filter clusters within a Confluent Cloud environment.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  environment:
    description:
      - Environment Id
    type: str
    required: True
  names:
    description:
      - List of cluster Names.
      - Mutually exclusive when used with `ids`
    type: list
    elements: str
  ids:
    description:
      - List of cluster Ids.
      - Mutually exclusive when used with `names`
    type: list
    elements: str
"""

EXAMPLES = """
- name: List all available clusters in a given environment
  confluent.cloud.cluster_info:
    environment: env-f3a90de
- name: List clusters that match the given Ids
  confluent.cloud.cluster_info:
    environment: env-f3a90de
    ids:
      - lkc-6wkr2
      - lkc-310rw
- name: List clusters that match the given Names
  confluent.cloud.cluster_info:
    environment: env-f3a90de
    names:
      - test
      - production
"""

RETURN = """
---
clusters:
  description: TODO Dictionary of matching clusters, keyed by cluster id
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
          description: The name of the cluster
          type: str
          returned: success
        api_endpoint:
          description: API endpoint
          type: str
          returned: success
          sample: https://pkac-4nd3z.us-west4.gcp.confluent.cloud
        http_endpoint:
          description: The cluster HTTP request UR
          type: str
          returned: success
          sample: https://pkc-lzvrd.us-west4.gcp.confluent.cloud:443
        kafka_bootstrap_endpoint:
          description: The bootstrap endpoint used by Kafka clients to connect to the cluster
          type: str
          returned: success
          sample: SASL_SSL://pkc-lzvrd.us-west4.gcp.confluent.cloud:9092
        availability:
          description: The availability zone configuration of the cluster
          type: str
          returned: success
          sample: SINGLE_ZONE
        cloud:
          description: The cloud service provider in which the cluster is running (AWS, GCP, AZURE)
          type: str
          returned: success
          sample: AWS
        region:
          description: The cloud service provider region where the cluster is running
          type: str
          returned: success
          sample: us-west4
        config:
          description: The configuration of the Kafka cluster.
          type: dict
          returned: success
          contains:
            kind:
              description: The configuration of the Kafka cluster.
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
          description: The status of the cluster
          type: dict
          returned: success
          contains:
            phase:
              description:
                - "The lifecyle phase of the cluster:"
                - "PROVISIONED: cluster is provisioned;"
                - "PROVISIONING: cluster provisioning is in progress;"
                - "FAILED: provisioning failed"
              type: str
              returned: success
              sample: PROVISIONED
            cku:
              description: The number of Confluent Kafka Units (CKUs) the Dedicated cluster currently has
              type: int
              returned: success
              sample: 1
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def get_clusters_info(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/cmk/v2/clusters",
    )

    resources = confluent.query(data={'environment': module.params.get('environment'), 'page_size': 100})

    if resources and module.params.get('ids'):
        clusters = [c for c in resources['data'] if c['id'] in module.params.get('ids')]
    elif resources and module.params.get('names'):
        clusters = [c for c in resources['data'] if c['spec']['display_name'] in module.params.get('names')]
    else:
        clusters = resources['data']

    return({'clusters': {c['id']: c for c in clusters}})


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['environment'] = dict(type='str', required=True)
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
        module.exit_json(**get_clusters_info(module))
    except Exception as e:
        module.fail_json(msg='failed to get cluster info, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
