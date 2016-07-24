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
      roles:
         - role: dieswaytoofast.ansible_aws
           ansible_aws_config_file: ansible_aws_params.yml

License
-------

BSD

Author Information
------------------

Mahesh Paolini-Subramanya (@dieswaytoofast)
