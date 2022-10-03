#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: cluster
short_description: Manage Confluent Cloud clusters
description:
  - Manage Confluent Cloud clusters.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  id:
    description: Cluster Id
    type: str
  name:
    description: 
      - Cluster name.
      - Mutation after creation requires supplying the cluster id.
    type: str
  state:
    description:
      - If `absent`, the cluster and all objects (connectors, service accounts) will be removed.
        Note that absent will not cause Cluster to fail if the Cluster does not exist.
      - If `present`, the cluster will be created.
    default: present
    choices:
      - absent
      - present
    type: str
  environment:
    description: 
      - The environment to which this belongs.
      - Immutable after deployment.
    type: str
    required: True
  availability:
    description: 
      - The availability zone configuration of the cluster.
      - Immutable after deployment.
    type: str
    choices:
      - SINGLE_ZONE
      - MULTI_ZONE
    default: SINGLE_ZONE
  cloud:
    description: 
      - The cloud service provider in which the cluster is running.
      - Immutable after deployment.
    type: str
    choices:
      - AWS
      - GCP
      - AZURE
    required: True
  region:
    description: 
      - The cloud service provider region where the cluster is running.
      - Immutable after deployment.
    type: str
    required: True
  kind:
    description: 
      - Cluster type.
      - Only Basic -> Standard changes are available after deployment.
    type: str
    default: Basic
    choices:
      - Basic
      - Standard
      - Dedicated
  cku:
    description: 
      - The number of Confluent Kafka Units (CKUs) for Dedicated cluster types. 
      - MULTI_ZONE dedicated clusters must have at least two CKUs.
    type: int
    default: 1
  encryption_key:
    description: 
      - The id of the encryption key that is used to encrypt the data in the Kafka cluster. (e.g. for Amazon Web Services, the Amazon Resource Name of the key).
      - Only available for Dedicated clusters.
    type: str
    required: True
  network:
    description: The network associated with this object.
    type: str
    required: True
"""

EXAMPLES = """
- name: Create new cluster
  confluent.cloud.cluster:
    state: present
    environment: env-f3a90de
    name: MyCluster
    availability: SINGLE_ZONE
    cloud: GCP
    region: us-west4
    kind: Basic
- name: Remove existing cluster (by id)
  confluent.cloud.cluster_info:
    state: absent
    environment: env-f3a90de
    id: lkc-6wkr2
- name: Remove existing cluster (by name)
  confluent.cloud.cluster_info:
    state: absent
    environment: env-f3a90de
    name: MyCluster
"""

RETURN = """
---
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
          description: The lifecyle phase of the cluster: PROVISIONED: cluster is provisioned; PROVISIONING: cluster provisioning is in progress; FAILED: provisioning failed
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
