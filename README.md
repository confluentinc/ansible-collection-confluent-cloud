
# Ansible collection for Confluent Cloud

This collection provides a series of Ansible modules for interacting the [Confluent Cloud](https://confluent.cloud).


## Installation

It is recommended to run ansible in [Virtualenv](https://virtualenv.pypa.io/en/latest/) 


## Requirements

- ansible version >= 2.9

To install the Confluent Cloud Ansible collection hosted in Galaxy:

```bash
ansible-galaxy collection install confluent.cloud
```

Install dependencies required by the collection (adjust path to collection if necessary):

To upgrade to the latest version of Confluent Cloud collection:

```bash
ansible-galaxy collection install confluent.cloud --force
```

## Usage

### Playbooks

To use a module from Confluent Cloud Ansible collection, please reference the full namespace, collection name, 
and modules name that you want to use:

```yaml
---
- name: Using Confluent Cloud Ansible collection
  hosts: localhost
  tasks:
    - name: Exec ping succeed
      confluent.cloud.ping:
```

Or you can add full namepsace and collecton name in the `collections` element:

```yaml
---
- name: Using Confluent Cloud Ansible collection
  hosts: localhost
  collections:
    - confluent.cloud
  tasks:
    - ping:
```


## Documentation

You can find example configurations in [examples](examples/)


## Contributing

There are many ways in which you can participate in the project, for example:

- Submit bugs and feature requests, and help us verify as they are checked in
- Review source code changes
- Review the documentation and make pull requests for anything from typos to new content
- If you are interested in fixing issues and contributing directly to the code base, please see the [CONTRIBUTING](CONTRIBUTING.md) document


## License

[Apache 2.0](docs/LICENSE.md)

