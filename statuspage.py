# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import sys, os
from github import Github
import click
from tqdm import tqdm

__version__ = "0.3pre"

try:
    ROOT = sys._MEIPASS
except AttributeError:
    ROOT = os.path.dirname(os.path.realpath(__file__))

COLORED_LABELS = (
    ("1192FC", "investigating",),
    ("FFA500", "degraded performance"),
    ("FF4D4D", "major outage", )
)

SYSTEM_LABEL_COLOR = "171717"

TEMPLATES = [
    "milligram.min.css",
    "style.css",
    "script.js",
    "mustache.min.js",
    "lockr.js",
    "index.html",
]


@click.group()
@click.version_option(__version__, '-v', '--version')
def cli():  # pragma: no cover
    pass


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--token', prompt='GitHub API Token', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--systems', prompt='Systems, eg (Website,API)', help='')
def create(token, name, systems, org):
    run_create(name=name, token=token, systems=systems, org=org)


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--token', prompt='GitHub API Token', help='')
def update(name, token, org):  # pragma: no cover
    click.echo("This function is no longer available since version 0.3.")

@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--token', prompt='GitHub API Token', help='')
def upgrade(name, token, org):
    run_upgrade(name, token, org)


def run_upgrade(name, token, org):

    gh = Github(token)
    entity, collaborators = get_user_info(gh, org)

    repo = entity.get_repo(name=name)

    ref_sha = repo.get_git_ref("heads/gh-pages").object.sha

    template = repo.get_file_contents(path="/template.html", ref=ref_sha)

    repo.delete_file(
        path="/template.html",
        message="upgrading to 0.3",
        sha=template.sha,
        branch="gh-pages"
    )

    for template in tqdm(["index.html", "style.css"], desc="Editing files"):
        with open(os.path.join(ROOT, "template", template), "r") as f:
            content = f.read()
            if template == "index.html":
                content = add_config(content, entity.login, name, collaborators)
            old = repo.get_file_contents("/" + template, ref_sha)
            repo.update_file(
                path="/" + template,
                message="upgrading to 0.3",
                content=content,
                branch="gh-pages",
                sha=old.sha,
            )

    for template in tqdm(["lockr.js", "mustache.min.js", "script.js"], desc="Uploading new files"):
        with open(os.path.join(ROOT, "template", template), "r") as f:
            repo.create_file(
                path="/" + template,
                message="upgrading to 0.3",
                content=f.read(),
                branch="gh-pages"
            )


def run_create(name, token, systems, org):
    gh = Github(token)

    entity, collaborators = get_user_info(gh, org)

    # create the repo
    repo = entity.create_repo(name=name)

    # get all labels an delete them
    for label in tqdm(list(repo.get_labels()), "Deleting initial labels"):
        label.delete()

    # create new status labels
    for color, label in tqdm(COLORED_LABELS, desc="Creating status labels"):
        repo.create_label(name=label, color=color)

    # create system labels
    for label in tqdm(systems.split(","), desc="Creating system labels"):
        repo.create_label(name=label.strip(), color=SYSTEM_LABEL_COLOR)

    # add an empty file to master, otherwise we won't be able to create the gh-pages
    # branch
    repo.create_file(
        path="/README.md",
        message="initial",
        content="Visit this site at https://{login}.github.io/{name}/".format(
            login=entity.login,
            name=name
        ),
    )

    # create the gh-pages branch
    ref = repo.get_git_ref("heads/master")
    repo.create_git_ref(ref="refs/heads/gh-pages", sha=ref.object.sha)

    # add all the template files to the gh-pages branch
    for template in tqdm(TEMPLATES, desc="Adding template files"):
        with open(os.path.join(ROOT, "template", template), "r") as f:
            content = f.read()
            if template == "index.html":
                content = add_config(content, entity.login, name, collaborators)
            repo.create_file(
                path="/" + template,
                message="initial",
                content=content,
                branch="gh-pages"
            )

    # set the gh-pages branch to be the default branch
    repo.edit(name=name, default_branch="gh-pages")

    click.echo("Create new issues at https://github.com/{login}/{name}/issues".format(
        login=entity.login,
        name=name
    ))
    click.echo("Visit your new status page at https://{login}.github.io/{name}/".format(
        login=entity.login,
        name=name
    ))


def add_config(content, login, name, collaborators):
    # add the config for this repo to index.html
    config = """{{"repo": "{login}/{name}", "collaborators": [{collaborators}], "v": "{v}"}}""".format(
            login=login,
            name=name,
            v=__version__,
            collaborators=",".join(["'{0}'".format(c) for c in collaborators]),
    )
    return content.replace("{{ config }}", config)


def get_user_info(gh, org):
    if org:
        entity = gh.get_organization(org)
        collaborators = [user.login for user in entity.get_members()]
        if not collaborators:
            click.echo("Unable to read collaborators for {org}. Please make sure to enable "
                       "read:org for this access token and try again".format(org=entity.name))
            sys.exit(-1)
    else:
        entity = gh.get_user()
        collaborators = [entity.login]
    return entity, collaborators


if __name__ == '__main__':  # pragma: no cover
    cli()