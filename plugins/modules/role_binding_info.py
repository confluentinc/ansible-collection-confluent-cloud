#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: role_binding_info
short_description: Get information on existing role bindings
description:
  - Enumerate and filter role bindings within a Confluent Cloud environment.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  resource_uri:
    description:
      - URI (crn://) associated with the resource in which to search
    type: str
    required: true
  roles:
    description:
      - List of roles to filter results by
      - Mutually exclusive when used with `principals`.
    type: list
    elements: str
  principals:
    description:
      - List of principals to filter results by
      - Mutually exclusive when used with `roles`.
    type: list
    elements: str
"""

EXAMPLES = """
- name: Get context for a specific environment
  confluent.cloud.environment_info:
    ids:
      - env-yoxp06
  register: result
- name: List all role bindings in a given environment
  confluent.cloud.role_binding_info:
    resource_uri: "{{ result.resource_uri }}"
- name: List all role bindings for a specific user in a given environment
  confluent.cloud.role_binding_info:
    resource_uri: "{{ result.resource_uri }}"
    principals:
      - User:u-l6xn83
- name: List all role bindings for with specific roles in a given environment
  confluent.cloud.role_binding_info:
    resource_uri: "{{ result.resource_uri }}"
    roles:
      - EnvironmentAdmin
      - MetricsViewer
"""

RETURN = """
---
role_bindings:
  description: Dictionary of matching role bindings, keyed by role binding id
  returned: success
  type: dict
  contains:
    id:
      description: Role binding id
      type: str
      returned: success
      sample: rb-y3mDg
    principal:
      description: Principal that role binding applies to
      type: str
      returned: success
      sample: User:u-l6xn83
    role:
      description: Role that role binding applies to
      type: str
      returned: success
      sample: EnvironmentAdmin
    metadata:
      description: User metadata, including create timestamp and updated timestamp
      type: dict
      returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def canonical_resource(resource):
    resource['role'] = resource['role_name']
    del(resource['role_name'])
    return(resource)


def get_role_bindings_info(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/role-bindings",
    )

    resources = confluent.query(data={'crn_pattern': module.params.get('resource_uri'), 'page_size': 100})

    if resources and module.params.get('principals'):
        role_bindings = [rb for rb in resources['data'] if rb['principal'] in module.params.get('principals')]
    elif resources and module.params.get('roles'):
        role_bindings = [rb for rb in resources['data'] if rb['role_name'] in module.params.get('roles')]
    else:
        role_bindings = resources['data']

    return({'role_bindings': {rb['id']: canonical_resource(rb) for rb in role_bindings}})


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['resource_uri'] = dict(type='str', required=True)
    argument_spec['principals'] = dict(type='list', elements='str')
    argument_spec['roles'] = dict(type='list', elements='str')

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(**get_role_bindings_info(module))
    except Exception as e:
        module.fail_json(msg='failed to get role_binding info, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
