#!/usr/bin/python3
#  encoding: utf-8
"""
Check ECR to see if a given version of the image exists in the repo
Notes:
    all_tags: json string in the form '{"all_tags" : ["a", "b", "c"]}'
"""
import json
import sys

from sarge import get_stdout, run

AWS = '/usr/local/bin/aws'
DOCKER = '/usr/bin/docker'


def get_image_ids_from_ecr(region: str=None, repo: str=None):
    """
    Get all the image ids from the ECR repo
    :param region:
    :param repo:
    :return:
    """
    if region is None:
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


def check_for_tag(image_ids: list=[], tag: str=None):
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


def get_tags_from_image_ids(image_ids: list=[]):
    """
    Get the tags for the given image_ids
    Note that nulls and 'latest' is ignored
    :param image_ids:
    :return:
    """
    tags = []

    for image in image_ids:
        if ('imageTag') in image:
            tag = image['imageTag']
            if (tag is None) or (tag == 'latest'):
                pass
            else:
                tags = tags + [tag]

    return tags


def get_tags_from_all_tags(all_tags: str=None):
    """
    Convert the incoming stringified JSON into a list of tags
    :param all_tags:
    :return:
    """
    all_tags_json =  '{"allTags" : ["' + all_tags.replace('\n', '","') + '"] }'
    json_output = json.loads(all_tags_json)
    if 'allTags' in json_output:
        return(json_output['allTags'])
    else:
        return([])


def get_tags_from_ecr(region: str=None, repo: str=None):
    """
    Get all the tags for the repo from ECR
    :param region:
    :param repo:
    :return:
    """
    # Get the image_ids from the registry
    image_ids = get_image_ids_from_ecr(region=region, repo=repo)

    # Get the tags from the image_ids
    tags = get_tags_from_image_ids(image_ids)

    return tags


def push_if_not_exist(region: str=None, registry_prefix: str=None, repo: str=None, tag: str=None):
    """
    Push the image to the registry if it doesn't exist
    :param region:
    :param registry_prefix:
    :param repo:
    :param tag:
    :return:
    """
    image_ids = get_image_ids_from_ecr(region=region, repo=repo)
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


def pull_if_not_exist(region: str=None, registry_prefix: str=None, repo: str=None, tag: str=None):
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

def prune_repos(region: str=None, registry_prefix: str=None, repo: str=None, current_tag: str=None, all_tags: str=None):
    """
    Pull the image from the registry if it doesn't exist locally
    :param region:
    :param registry_prefix:
    :param repo:
    :param current_tag:
    :param all_tags:
    :return:
    """
    # Get the tags from the all_tags JSON
    all_tags_list = get_tags_from_all_tags(all_tags)

    # Add the current_tag to the recent (local) tags. Just to be safe
    recent_tags = all_tags_list + [current_tag]

    # Get the tags for the repo from ECR
    ecr_tags = get_tags_from_ecr(region, repo)

    # Get all the tags in the registry that are *not* the ones we want
    bad_tags = [tag for tag in ecr_tags if tag not in recent_tags]

    # Delete the obsolete images
    for tag in bad_tags:
        output = get_stdout('''{AWS} ecr batch-delete-image --region {region} --repository-name {repo} --image-ids imageTag={tag}'''
                            .format(AWS=AWS, region=region, repo=repo, tag=tag))

    return True


def get_args(argv: list=[]):
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
        all_tags = sys.argv[6]
        return command, region, registry_prefix, repo, tag, all_tags
    except IndexError:
        all_tags = None
    except:
        sys.exit("Whyfor you not send in args?")


command, region, registry_prefix, repo, tag, all_tags = get_args(sys.argv)
if command == "push":
    retval = push_if_not_exist(region=region, registry_prefix=registry_prefix, repo=repo, tag=tag)
    if not retval:
        print('FAILED')
elif command == "pull":
    retval = pull_if_not_exist(region=region, registry_prefix=registry_prefix, repo=repo, tag=tag)
    if not retval:
        print('FAILED')
elif command == "prune":
    # If an empty list is passed in for all_tags, fail violently
    if all_tags is None:
        print('FAILED')
    else:
        retval = prune_repos(region=region, registry_prefix=registry_prefix, repo=repo, current_tag=tag, all_tags=all_tags)
        if not retval:
            print('FAILED')
else:
    print('FAILED')
