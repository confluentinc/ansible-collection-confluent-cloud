#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re

DOCUMENTATION = """
---
module: role_binding
short_description: Manage Confluent Cloud role bindings
description:
  - Manage Confluent Cloud role bindings within a Confluent Cloud environment.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  id:
    description: Role binding Id
    type: str
  resource_uri:
    description:
      - URI (crn://) associated with the resource in which to search
      - Note that the `crn` URI associated with some resources may need to be modified to be
        accepted as a as the `resource_uri`.  Review examples for how to modify the cluster
        `crn`.
    type: str
  role:
    description: 
      - Role.  `resource_uri` may change based on the scope of the role being added.
      - Available roles are `OrganizationAdmin`, `EnvironmentAdmin`, `CloudClusterAdmin`,
        `Operator`, `NetworkAdmin`, `MetricsViewer`, `ResourceOwner`, `DeveloperManage`,
        `DeveloperRead`, `DeveloperWrite`, and `KsqlAdmin`.  
        [View details on roles here](https://docs.confluent.io/cloud/current/access-management/access-control/cloud-rbac.html#ccloud-rbac-roles).
    type: str
  principal:
    description: Role
    type: str
  state:
    description:
      - If `absent`, the service account will be removed.
        Note that absent will not cause Role Binding to fail if the Role Binding does not exist.
      - If `present`, the service account will be created.
    default: present
    choices:
      - absent
      - present
    type: str
"""

EXAMPLES = """
- name: Get context for a specific environment
  confluent.cloud.environment_info:
    ids:
      - env-yoxp06
  register: result
- name: Create new role binding
  confluent.cloud.role_binding:
    role: EnvironmentAdmin
    principal: sa-j31z28
    resource_uri: "{{ result.resource_uri }}"
    state: present
- name: Delete role_binding
  confluent.cloud.role_binding:
    role: EnvironmentAdmin
    principal: sa-j31z28
    resource_uri: "{{ result.resource_uri }}"
    state: absent
- name: Delete role_binding (by id)
    id: rb-jhz28
    state: absent

# Modifying crn associated with the cluster for use in role binding
- name: Get cluster
  confluent.cloud.cluster_info:
    environment: env-12m16j
    ids:
      - lkc-7yxkd2
  register: result
- name: Create role binding
  confluent.cloud.role_binding:
    resource_uri: "{{ result.resource_uri | regex_replace('/kafka=.*?$', '') }}"
    principal: sa-j31z28
    role: CloudClusterAdmin
    state: present
"""

RETURN = """
---
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


def role_binding_remove(module, resource_id):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/role-bindings",
        resource_key_id=resource_id
    )

    return(confluent.absent())


def role_binding_create(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/role-bindings",
    )

    return(canonical_resource(confluent.create({
        'principal': module.params.get('principal'),
        'role_name': module.params.get('role'),
        'crn_pattern': module.params.get('resource_uri'),
    })))


def get_role_bindings(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/role-bindings",
    )

    resources = confluent.query(data={'crn_pattern': module.params.get('resource_uri'), 'page_size': 100})

    return(resources['data'])


def role_binding_process(module):
    # Get existing role_binding if it exists
    role_bindings = get_role_bindings(module)

    if module.params.get('id') and len([rb for rb in role_bindings if rb['id'] == module.params.get('id')]):
        role_binding = [rb for rb in role_bindings if rb['id'] == module.params.get('id')][0]
    elif module.params.get('role') and module.params.get('principal') and len([rb for rb in role_bindings if rb['role_name'] == module.params.get('role') and rb['principal'] == module.params.get('principal')]):
        role_binding = [rb for rb in role_bindings if rb['role_name'] == module.params.get('role') and rb['principal'] == module.params.get('principal')][0]
    else:
        role_binding = None

    # Manage role_binding removal
    if module.params.get('state') == 'absent' and not role_binding:
        return({"changed": False})
    elif module.params.get('state') == 'absent' and role_binding:
        return(role_binding_remove(module, role_binding['id']))

    # Create role_binding
    elif module.params.get('state') == 'present' and not role_binding:
        return(role_binding_create(module))

    # Immutable resource is present
    else:
        return(canonical_resource(role_binding))


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['id'] = dict(type='str')
    argument_spec['resource_uri'] = dict(type='str', required=True)
    argument_spec['role'] = dict(type='str')
    argument_spec['principal'] = dict(type='str')
    argument_spec['state'] = dict(default='present', choices=['present', 'absent'])

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if module.params.get('principal'):
        if re.match("(u|sa)",module.params.get('principal')):
            module.params['principal'] = "User:" + module.params.get('principal')


    try:
        module.exit_json(**role_binding_process(module))
    except Exception as e:
        module.fail_json(msg='failed to process role_binding, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
