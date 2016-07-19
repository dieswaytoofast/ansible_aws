#!/usr/bin/python3
#  encoding: utf-8
"""
Check ECR to see if a given version of the image exists in the repo
"""
import json
import sys

from sarge import get_stdout, run

AWS = '/usr/local/bin/aws'
DOCKER = '/usr/bin/docker'


def get_image_ids_from_ecr(region: str=None, repo: str=None, tag: str=None):
    """
    Get all the image ids from the ECR repo
    :param region:
    :param repo:
    :param tag:
    :return:
    """
    if region is None:
        return False
    if tag is None:
        return False

    if repo is None:
        return False
    else:
        output = get_stdout('''{AWS} ecr list-images --region {region} --repository-name {repo}'''
                            .format(AWS=AWS, region=region, repo=repo))

    json_output = json.loads(output)
    if 'imageIds' in json_output:
        return(json_output['imageIds'])
    else:
        return([])


def check_for_tag(image_ids, tag):
    """
    Check to see if the given tag is in the image_ids
    :param image_ids:
    :param tag:
    :return:
    """
    for image in image_ids:
        if ('imageTag') in image:
            if image['imageTag'] == tag:
                return True
    return False


def push_if_not_exist(region, registry_prefix, repo, tag):
    """
    Push the image to the registry if it doesn't exist
    :param region:
    :param registry_prefix:
    :param repo:
    :param tag:
    :return:
    """
    image_ids = get_image_ids_from_ecr(region=region, repo=repo, tag=tag)
    if not check_for_tag(image_ids=image_ids, tag=tag):
        # Make sure image exists, else NoOp
        image_exists = get_stdout('''{docker} images -q {repo}'''.format(docker=DOCKER,
                                                                         repo=repo))
        if not image_exists:
            return(False)
        target = '''{registry_prefix}/{repo}:{tag}'''.format(registry_prefix=registry_prefix,
                                                             repo=repo,
                                                             tag=tag)
        # Tag the repo
        run('''{docker} tag {repo} {target}'''.format(docker=DOCKER,
                                                      repo=repo,
                                                      target=target))
        # And push it to the registry
        run('''{docker} push {target}'''.format(docker=DOCKER, target=target))

    return(True)


def pull_if_not_exist(region, registry_prefix, repo, tag):
    """
    Pull the image from the registry if it doesn't exist locally
    :param region:
    :param registry_prefix:
    :param repo:
    :param tag:
    :return:
    """

    output = get_stdout('''{docker} images {repo}:{tag}'''.format(docker=DOCKER,
                                                                  repo=repo,
                                                                  tag=tag))

    if repo not in output:
        target = '''{registry_prefix}/{repo}:{tag}'''.format(registry_prefix=registry_prefix,
                                                             repo=repo,
                                                             tag=tag)
        # And push it to the registry
        run('''{docker} pull {target}'''.format(docker=DOCKER,
                                                target=target))

        # Tag the repo back to the unqualified name
        run('''{docker} tag {target} {repo}'''.format(docker=DOCKER,
                                                      repo=repo,
                                                      target=target))
        # Tag the repo back to be 'latest'
        run('''{docker} tag {target} {repo}:latest'''.format(docker=DOCKER,
                                                             repo=repo,
                                                             target=target))
        # Tag the repo back to the correct tag
        run('''{docker} tag {target} {repo}:{tag}'''.format(docker=DOCKER,
                                                            repo=repo,
                                                            tag=tag,
                                                            target=target))

    return(True)


def get_args(argv: list=None):
    """
    Make sure that we got what we need, and use it
    :param argv:
    :return:
    """
    try:
        command = sys.argv[1]
        region = sys.argv[2]
        registry_prefix = sys.argv[3]
        repo = sys.argv[4]
        tag = sys.argv[5]
        return command, region, registry_prefix, repo, tag
    except:
        sys.exit("Whyfor you not send in args?")


command, region, registry_prefix, repo, tag = get_args(sys.argv)
if command == "push":
    retval = push_if_not_exist(region=region, registry_prefix=registry_prefix, repo=repo, tag=tag)
    if not retval:
        print('FAILED')
elif command == "pull":
    retval = pull_if_not_exist(region=region, registry_prefix=registry_prefix, repo=repo, tag=tag)
    if not retval:
        print('FAILED')
else:
    print('FAILED')
