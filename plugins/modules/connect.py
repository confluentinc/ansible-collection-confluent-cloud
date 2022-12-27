#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: connect
short_description: Manage Confluent Cloud Connectors
description:
  - Manage Confluent Cloud connectors
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  environment:
    description:
      - Environment Id.
  cluster:
    description:
      - Cluster Id.
    type: str
  name:
    description:
      - Unique connector name
    type: str
  kafka_key:
    description:
      - Kafka API user key with access to the topics this connector will access.
      - Note this is different than the Cloud Key which is used to mutate Confluent
        Cloud resources.
    type: str
  kafka_secret:
    description:
      - Kafka API user secret with access to the topics this connector will access.
      - Note this is different than the Cloud Key which is used to mutate Confluent
        Cloud resources.
    type: str
  connector:
    description:
      - The connector class name. E.g. DatagenSource, BigQuerySink, GcsSink, etc.
    type: str
  state:
    description:
      - If `absent`, the connector will be removed.
      - If `present`, the connector will be created.
      - If `pause`, the connector will be paused.
      - If `resume`, the connector will be resumed.
    default: present
    choices:
      - absent
      - present
      - pause
      - resume
    type: str
  props:
    description:
      - Dictionary of connector-specific properties.  These properties vary by connector
    type: str
"""

EXAMPLES = """
- name: Create Datagen connector
  confluent.cloud.connect:
    name: datagen_source
    environment: env-f3a90de
    cluster: lkc-6wkr2
    connector: DatagenSource
    kafka_key: QMQ6AOEJISDAG6FI
    kafka_secret: aeXANrbGCLqzfl6Q7k2Ygi5cSrS+F97TThNTZMSP0AvzF+g8l4iG3PcDJleVrHD8
    props:
      kafka.auth.mode: KAFKA_API_KEY
      kafka.topic: pageviews
      quickstart: PAGEVIEWS
      max.interval: "1200"
      iterations: "100000000"
      output.data.format: JSON
      tasks.max: "1"
    state: present
- name: Pause existing connector by name
  confluent.cloud.connect:
    environment: env-f3a90de
    cluster: lkc-6wkr2
    name: datagen_source
    state: pause
- name: Resume existing connector by name
  confluent.cloud.connect:
    environment: env-f3a90de
    cluster: lkc-6wkr2
    name: datagen_source
    state: resume
- name: Delete existing connector by name
  confluent.cloud.connect:
    environment: env-f3a90de
    cluster: lkc-6wkr2
    name: datagen_source
    state: absent
"""

RETURN = """
---
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
    return(resource)


def connect_remove(module, resource_id):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/connect/v1/environments/%s/clusters/%s/connectors" % (
            module.params.get('environment'),
            module.params.get('cluster')
        ),
        resource_key_id=resource_id
    )

    return(confluent.absent())


def connect_pause(module, resource_id):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/connect/v1/environments/%s/clusters/%s/connectors/%s/pause" % (
            module.params.get('environment'),
            module.params.get('cluster'),
            module.params.get('name'),
        ),
    )

    return(confluent.query(method='PUT'))


def connect_resume(module, resource_id):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/connect/v1/environments/%s/clusters/%s/connectors/%s/resume" % (
            module.params.get('environment'),
            module.params.get('cluster'),
            module.params.get('name'),
        ),
    )

    return(confluent.query(method='PUT'))


def connect_create(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/connect/v1/environments/%s/clusters/%s/connectors" % (
            module.params.get('environment'),
            module.params.get('cluster')
        )
    )

    config_base = {
            'name': module.params.get('name'),
            'kafka.api.key': module.params.get('kafka_key'),
            'kafka.api.secret': module.params.get('kafka_secret'),
            'connector.class': module.params.get('connector')
    }
    config = { **config_base, **module.params.get('props') }

    return(canonical_resource(confluent.create({
        'name': module.params.get('name'),
        'config': config,
    })))


def connect_update(module, connector):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/connect/v1/environments/%s/clusters/%s/connectors/%s" % (
            module.params.get('environment'),
            module.params.get('cluster'),
            module.params.get('name'),
        ),
        resource_key_id='config',
        resource_update_method='PUT',
    )

    config_base = {
            'name': module.params.get('name'),
            'kafka.api.key': module.params.get('kafka_key'),
            'kafka.api.secret': module.params.get('kafka_secret'),
            'connector.class': module.params.get('connector')
    }
    config = { **config_base, **module.params.get('props') }

    return(canonical_resource(confluent.update(connector['info']['config'],config,required=config)))


def get_connectors(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/connect/v1/environments/%s/clusters/%s/connectors" % (
            module.params.get('environment'),
            module.params.get('cluster'),
        )
    )

    resources = confluent.query(data={'expand': 'status,info', 'page_size': 100})

    return(resources)


def connect_process(module):
    # Get existing connect if it exists
    connectors = get_connectors(module)
    if module.params.get('name') in connectors:
        connector = connectors[module.params.get('name')]
    else:
        connector = None

    # Manage connect removal
    if module.params.get('state') == 'absent' and not connector:
        return({"changed": False})
    elif module.params.get('state') == 'absent' and connector:
        return(connect_remove(module, connector['info']['name']))
    elif module.params.get('state') == 'pause' and connector:
        return(connect_pause(module, connector['info']['name']))
    elif module.params.get('state') == 'resume' and connector:
        return(connect_resume(module, connector['info']['name']))

    # Create connect
    elif module.params.get('state') == 'present' and not connector:
        return(connect_create(module))

    # Check for update
    else:
        return(connect_update(module, connector))


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['environment'] = dict(type='str', required=True)
    argument_spec['cluster'] = dict(type='str', required=True)
    argument_spec['name'] = dict(type='str', required=True)
    argument_spec['state'] = dict(default='present', choices=['present', 'absent', 'pause', 'resume'])
    argument_spec['kafka_key'] = dict(type='str')
    argument_spec['kafka_secret'] = dict(type='str', no_log=True)
    argument_spec['connector'] = dict(type='str')
    argument_spec['props'] = dict(type='dict')

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(**connect_process(module))
    except Exception as e:
        module.fail_json(msg='failed to process connect, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
