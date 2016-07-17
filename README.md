Role Name
=========

Collection of utils to deal with AWS

Requirements
------------

Requires Ansible 2.0 or higher.

Role Variables
--------------



Dependencies
------------

ansible_weave

Example Playbook
----------------

You'll need to edit *ansible_aws_params.yml* to put in params relevant to you
(An example is provided)

    - hosts: foo
      include_vars: ansible_aws_params.yml
      roles:
         - role: dieswaytoofast.ansible_aws

License
-------

BSD

Author Information
------------------

Mahesh Paolini-Subramanya (@dieswaytoofast)
