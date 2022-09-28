# -*- coding: utf-8 -*-
# Copyright (c) 2022, Keith Resar <kresar@confluent.io>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re
import random
import time
import base64
import urllib

from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.basic import env_fallback
from ansible.module_utils.urls import fetch_url

CONFLUENT_USER_AGENT = "Ansible Confluent Cloud v1"


def confluent_argument_spec():
    return dict(
        api_endpoint=dict(
            type="str",
            fallback=(env_fallback, ["CONFLUENT_API_ENDPOINT"]),
            default="https://api.confluent.cloud",
        ),
        api_key=dict(
            type="str",
            fallback=(env_fallback, ["CONFLUENT_API_KEY"]),
            required=True,
            no_log=False,
        ),
        api_secret=dict(
            type="str",
            fallback=(env_fallback, ["CONFLUENT_API_SECRET"]),
            no_log=True,
            required=True,
        ),
        api_timeout=dict(
            type="int",
            fallback=(env_fallback, ["CONFLUENT_API_TIMEOUT"]),
            default=60,
        ),
        api_retries=dict(type="int", fallback=(env_fallback, ["CONFLUENT_API_RETRIES"]), default=5),
        api_retry_max_delay=dict(
            type="int",
            fallback=(env_fallback, ["CONFLUENT_API_RETRY_MAX_DELAY"]),
            default=12,
        ),
        validate_certs=dict(
            type="bool",
            default=True,
        ),
    )


def backoff(retry, retry_max_delay=12):
    randomness = random.randint(0, 1000) / 1000.0
    delay = 2**retry + randomness
    if delay > retry_max_delay:
        delay = retry_max_delay + randomness
    time.sleep(delay)


class AnsibleConfluent:
    def __init__(
        self,
        module,
        resource_path,
        resource_key_name=None,
        resource_key_id="id",
        resource_create_param_keys=None,
        resource_update_param_keys=None,
        resource_update_method="PATCH",
    ):

        self.module = module

        # The API resource path e.g /ssh-keys
        self.resource_path = resource_path

        # The name key of the resource, usually 'name'
        self.resource_key_name = resource_key_name

        # The name key of the resource, usually 'id'
        self.resource_key_id = resource_key_id

        # Some resources have PUT, many have PATCH
        self.resource_update_method = resource_update_method

        auth = "%s:%s" % (self.module.params["api_key"],
                          self.module.params["api_secret"])
        self.headers = {
            "Authorization": "Basic %s" % (base64.standard_b64encode(auth.encode()).decode()),
            "User-Agent": CONFLUENT_USER_AGENT,
            "Accept": "application/json",
        }

        # Hook custom configurations
        self.configure()

    def configure(self):
        pass

    def api_next_page(self, uri):

        info = dict()
        resp_body = None
        for retry in range(0, self.module.params["api_retries"]):
            resp, info = fetch_url(
                self.module,
                uri,
                headers=self.headers,
                timeout=self.module.params["api_timeout"],
            )

            resp_body = resp.read() if resp is not None else ""

            # Check for 429 Too Many Requests
            if info["status"] != 429:
                break

            # Confluent Cloud has a rate limiting requests per second, try to
            # be polite.  Use exponential backoff plus a little bit of randomness
            backoff(retry=retry, retry_max_delay=self.module.params["api_retry_max_delay"])

        if info["status"] in (200, 201, 202):
            # Request subsequent page if next
            resp = self.module.from_json(to_text(resp_body, errors="surrogate_or_strict"))
            if 'metadata' in resp and 'next' in resp['metadata']:
                resp['data'] += self.api_next_page(resp['metadata']['next'])

            return(resp['data'])

        else:
            return([])

    def api_query(self, path, method="GET", data=None):

        if method == "GET" and data:
            data_encoded = data.copy()
            try:
                data = urllib.urlencode(data_encoded)
            except AttributeError:
                data = urllib.parse.urlencode(data_encoded)
        else:
            data = self.module.jsonify(data)

        info = dict()
        resp_body = None
        for retry in range(0, self.module.params["api_retries"]):
            resp, info = fetch_url(
                self.module,
                self.module.params["api_endpoint"] + path,
                method=method,
                data=data,
                headers=self.headers,
                timeout=self.module.params["api_timeout"],
            )

            resp_body = resp.read() if resp is not None else ""

            # Check for 429 Too Many Requests
            if info["status"] != 429:
                break

            # Confluent Cloud has a rate limiting requests per second, try to
            # be polite.  Use exponential backoff plus a little bit of randomness
            backoff(retry=retry, retry_max_delay=self.module.params["api_retry_max_delay"])

        # Success with content
        if info["status"] in (200, 201, 202):
            # Request subsequent page if next
            resp = self.module.from_json(to_text(resp_body, errors="surrogate_or_strict"))
            if 'metadata' in resp and 'next' in resp['metadata']:
                resp['data'] += self.api_next_page(resp['metadata']['next'])

            return(resp)

        # Success without content
        if info["status"] in (404, 204):
            return dict()

        self.module.fail_json(
            msg='Failure while calling the Confluent Cloud API with %s for "%s".' % (method, path),
            fetch_url_info=info,
        )

#    def query_filter_list_by_name(
#        self,
#        path,
#        key_name,
#        result_key,
#        param_key=None,
#        key_id=None,
#        query_params=None,
#        get_details=False,
#        fail_not_found=False,
#    ):
#        param_value = self.module.params.get(param_key or key_name)
#
#        found = dict()
#        for resource in self.query_list(path=path, result_key=result_key, query_params=query_params):
#            if resource.get(key_name) == param_value:
#                if found:
#                    self.module.fail_json(msg="More than one record with name=%s found. " "Use multiple=yes if module supports it." % param_value)
#                found = resource
#        if found:
#            if get_details:
#                return self.query_by_id(resource_id=found[key_id])
#            else:
#                return found
#
#        elif fail_not_found:
#            self.module.fail_json(msg="No Resource %s with %s found: %s" % (path, key_name, param_value))
#
#        return dict()

#    def query_filter_list(self):
#        # Returns a single dict representing the resource queryied by name
#        return self.query_filter_list_by_name(
#            key_name=self.resource_key_name,
#            key_id=self.resource_key_id,
#            get_details=self.resource_get_details,
#            path=self.resource_path,
#            result_key=self.resource_result_key_plural,
#        )

#    def query_by_id(self, resource_id=None, path=None, result_key=None):
#        # Defaults
#        path = path or self.resource_path
#
#        resource = self.api_query(path="%s%s" % (path, "/" + resource_id if resource_id else resource_id))
#        if resource:
#            return resource[result_key]
#
#        return dict()

    def query(self):
        # Returns a single dict representing the resource
        resources = self.api_query(path=self.resource_path)
        return(resources)

#    def query_list(self, path=None, result_key=None, query_params=None):
#        # Defaults
#        path = path or self.resource_path
#        result_key = result_key or self.resource_result_key_plural
#
#        resources = self.api_query(path=path, data=query_params)
#       #return resources[result_key] if resources else []
#       #self.module.fail_json(
#       #    msg='',
#       #    fetch_url_info=resources,
#       #)
#        return resources['data'] if resources else []

#    """
#    def wait_for_state(self, resource, key, state, cmp="="):
#        for retry in range(0, 30):
#            resource = self.query_by_id(resource_id=resource[self.resource_key_id])
#            if cmp == "=":
#                if key not in resource or resource[key] == state or not resource[key]:
#                    break
#            else:
#                if key not in resource or resource[key] != state or not resource[key]:
#                    break
#            backoff(retry=retry)
#        else:
#            self.module.fail_json(msg="Wait for %s to become %s timed out" % (key, state))
#
#        return resource
#    """

#    def create_or_update(self):
#        resource = self.query()
#        if not resource:
#            resource = self.create()
#        else:
#            resource = self.update(resource)
#        return resource

#    def present(self):
#        self.get_result(self.create_or_update())

    def create(self, data):
        resource = dict()

        if not self.module.check_mode:
            resource = self.api_query(
                path=self.resource_path,
                method="POST",
                data=data,
            )
        resource['changed'] = True
        return(resource)

    def update(self, cur_state, target_state):
        resource = {'changed': False}

        for key in target_state.keys():
            if key not in cur_state or cur_state[key] != target_state[key]:
                resource['changed'] = True
                break

        if resource["changed"]:
            if not self.module.check_mode:
                resource = self.api_query(
                    path="%s/%s" % (self.resource_path, self.resource_key_id),
                    method=self.resource_update_method,
                    data=target_state,
                )
                resource['changed'] = True

        return(resource)

    def absent(self):
        if not self.module.check_mode:
            self.api_query(
                path="%s/%s" % (self.resource_path, self.resource_key_id),
                method="DELETE",
            )
        return({'changed': True, 'id': self.resource_key_id})
