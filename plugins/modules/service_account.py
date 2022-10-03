#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: service_account
short_description: Manage existing Confluent Cloud service accounts
description:
  - Manage existing Confluent Cloud service_accounts within a Confluent Cloud environment.
  - Note this is different than service_accounts which uses its own module.
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
options:
  id:
    description: Service Account Id
    type: str
  name:
    description:
      - A human-readable name for the Service Account
      - Cannot be changed after creation
    type: str
  description:
    description:
      - A free-form description of the Service Account
    type: str
  state:
    description:
      - If `absent`, the service account will be removed.
        Note that absent will not cause Service Account to fail if the Service Account does not exist.
      - If `present`, the service account will be created.
    default: present
    choices:
      - absent
      - present
    type: str
"""

EXAMPLES = """
- name: Create new service account
  confluent.cloud.service account:
    name: application_1
    description: Service account for application 1
    state: present
- name: Modify service account
  confluent.cloud.service account:
    id: sa-j31z28
    name: application_new_name
    state: present
- name: Delete service account (by id)
  confluent.cloud.service_account:
    id: sa-j31z28
    state: absent
- name: Delete service account (by name)
  confluent.cloud.service_account:
    name: application_1
    state: absent
"""

RETURN = """
---
id:
  description: Service account id
  type: str
  returned: success
  sample: sa-lz51vz
name:
  description: A human-readable name for the Service Account
  type: str
  returned: success
  sample: application_1
description:
  description: A free-form description of the Service Account
  type: str
  returned: success
  sample: Service account for Application 1
metadata:
  description: User metadata, including create timestamp and updated timestamp
  type: dict
  returned: success
"""

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def service_account_remove(module, resource_id):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/service-accounts",
        resource_key_id=resource_id
    )

    return(confluent.absent())


def service_account_update(module, service_account):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/service-accounts",
        resource_key_id=service_account['id']
    )

    return(confluent.update(service_account, {
        'description': module.params.get('description'),
    }))


def service_account_create(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/service-accounts",
    )

    return(confluent.create({
        'display_name': module.params.get('name'),
        'description': module.params.get('description'),
    }))


def get_service_accounts(module):
    confluent = AnsibleConfluent(
        module=module,
        resource_path="/iam/v2/service-accounts",
    )

    resources = confluent.query(data={'page_size': 100})

    return(resources['data'])


def service_account_process(module):
    # Get existing service_account if it exists
    service_accounts = get_service_accounts(module)

    if module.params.get('id') and len([u for u in service_accounts if u['id'] == module.params.get('id')]):
        service_account = [sa for sa in service_accounts if sa['id'] == module.params.get('id')][0]
    elif module.params.get('name') and len([u for u in service_accounts if u['display_name'] == module.params.get('name')]):
        service_account = [sa for sa in service_accounts if sa['display_name'] == module.params.get('name')][0]
    else:
        service_account = None

    # Manage service_account removal
    if module.params.get('state') == 'absent' and not service_account:
        return({"changed": False})
    elif module.params.get('state') == 'absent' and service_account:
        return(service_account_remove(module, service_account['id']))

    # Create service_account
    elif module.params.get('state') == 'present' and not service_account:
        return(service_account_create(module))

    # Check for update
    else:
        return(service_account_update(module, service_account))


def main():
    argument_spec = confluent_argument_spec()
    argument_spec['id'] = dict(type='str')
    argument_spec['name'] = dict(type='str')
    argument_spec['description'] = dict(type='str')
    argument_spec['state'] = dict(default='present', choices=['present', 'absent'])

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    try:
        module.exit_json(**service_account_process(module))
    except Exception as e:
        module.fail_json(msg='failed to process service_account, error: %s' %
                         (to_native(e)), exception=traceback.format_exc())


if __name__ == "__main__":
    main()
