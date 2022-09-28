#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: ping
short_description: Verify module connectivity
description:
  - Verify connectivity and auth the Confluent Cloud API endpoint
version_added: "0.0.1"
author: "Keith Resar (@keithresar)"
extends_documentation_fragment:
  - confluent.cloud.confluent
"""

EXAMPLES = """
- name: Verify connectivity
  confluent.cloud.ping:
"""

RETURN = """
---
ping:
  description: Response
  returned: success
  type: str
  sample: pong
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.confluent.cloud.plugins.module_utils.confluent_api import AnsibleConfluent, confluent_argument_spec


def main():
    argument_spec = confluent_argument_spec()

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    confluent = AnsibleConfluent(
        module=module,
        resource_path="/org/v2/environments",
    )

    resources = confluent.query()

    if 'kind' in resources and resources['kind'] == 'EnvironmentList':
        confluent.module.exit_json(changed=False, ping="pong")
    else:
        module.fail_json(
            msg='Ping failure',
            fetch_url_info=resources,
        )


if __name__ == "__main__":
    main()
