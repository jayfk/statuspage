# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys, os
from datetime import datetime, timedelta

from github import Github, UnknownObjectException
import click
from jinja2 import Template
from tqdm import tqdm

__version__ = "0.3.1"

try:
    ROOT = sys._MEIPASS
except AttributeError:
    ROOT = os.path.dirname(os.path.realpath(__file__))

COLORED_LABELS = (
    ("1192FC", "investigating",),
    ("FFA500", "degraded performance"),
    ("FF4D4D", "major outage", )
)

STATUSES = [status for _, status in COLORED_LABELS]

SYSTEM_LABEL_COLOR = "171717"

TEMPLATES = [
    "template.html",
    "milligram.min.css",
    "style.css"
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
def update(name, token, org):
    run_update(name=name, token=token, org=org)


def run_update(name, token, org):
    click.echo("Generating..")
    gh = Github(token)
    if org:
        repo = gh.get_organization(org).get_repo(name=name)
    else:
        repo = gh.get_user().get_repo(name=name)

    # get a list of collaborators for this repo
    collaborators = [col.login for col in repo.get_collaborators()]

    systems, incidents, panels = {}, [], {}

    # get all systems and mark them as operational
    for name in iter_systems(labels=repo.get_labels()):
        systems[name] = {
            "status": "operational",
        }

    # loop over all issues in the past 90 days to get current and past incidents
    for issue in repo.get_issues(state="all", since=datetime.now() - timedelta(days=90)):
        labels = issue.get_labels()
        affected_systems = list(iter_systems(labels))
        severity = get_severity(labels)

        # make sure that non-labeled issues are not displayed
        if not affected_systems or severity is None:
            continue

        # make sure that the user that created the issue is a collaborator
        if issue.user.login not in collaborators:
            continue

        if issue.state == "open":
            # shit is hitting the fan RIGHT NOW. Mark all affected systems
            for affected_system in affected_systems:
                systems[affected_system]["status"] = severity

        # create an incident
        incident = {
            "created": issue.created_at,
            "title": issue.title,
            "systems": affected_systems,
            "severity": severity,
            "closed": issue.state == "closed",
            "body": issue.body,
            "updates": []
        }

        for comment in issue.get_comments():
            # add comments by collaborators only
            if comment.user.login in collaborators:
                incident["updates"].append({
                    "created": comment.created_at,
                    "body": comment.body
                })

        incidents.append(incident)

    # sort incidents by date
    incidents = sorted(incidents, key=lambda i: i["created"], reverse=True)

    # initialize and fill the panels with affected systems
    for system, data in systems.items():
        if data["status"] != "operational":
            if data["status"] in panels:
                panels[data["status"]].append(system)
            else:
                panels[data["status"]] = [system, ]

    # get the SHA of the current HEAD
    sha = repo.get_git_ref("heads/gh-pages").object.sha

    # get the template from the repo
    template_file = repo.get_file_contents(
        path="/template.html",
        ref=sha
    )

    # render the template
    template = Template(template_file.decoded_content.decode("utf-8"))
    content = template.render({
        "systems": systems, "incidents": incidents, "panels": panels
    })

    # create/update the index.html with the template
    try:
        # get the index.html file, we need the sha to update it
        index = repo.get_file_contents(
            path="/index.html",
            ref=sha,
        )

        repo.update_file(
            path="/index.html",
            sha=index.sha,
            message="update index",
            content=content,
            branch="gh-pages"
        )
    except UnknownObjectException:
        # index.html does not exist, create it
        repo.create_file(
            path="/index.html",
            message="initial",
            content=content,
            branch="gh-pages",
        )


def run_create(name, token, systems, org):
    gh = Github(token)

    if org:
        entity = gh.get_organization(org)
    else:
        entity = gh.get_user()

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
            repo.create_file(
                path="/" + template,
                message="initial",
                content=f.read(),
                branch="gh-pages"
            )

    # set the gh-pages branch to be the default branch
    repo.edit(name=name, default_branch="gh-pages")

    # run an initial update to add content to the index
    run_update(token=token, name=name, org=org)

    click.echo("Create new issues at https://github.com/{login}/{name}/issues".format(
        login=entity.login,
        name=name
    ))
    click.echo("Visit your new status page at https://{login}.github.io/{name}/".format(
        login=entity.login,
        name=name
    ))

    click.echo("")
    click.echo("###############################################################################")
    click.echo("# IMPORTANT: Whenever you add or close an issue you have to run the update    #")
    click.echo("# command to show the changes reflected on your status page.                  #")
    click.echo("# Here's a one-off command for this repo to safe it somewhere safe:           #")
    click.echo("# statuspage update --name={name} --token={token} {org}".format(
            name=name, token=token, org="--org=" + entity.login if org else ""))
    click.echo("###############################################################################")


def iter_systems(labels):
    for label in labels:
        if label.color == SYSTEM_LABEL_COLOR:
            yield label.name


def get_severity(labels):
    label_map = dict(COLORED_LABELS)
    for label in labels:
        if label.color in label_map:
            return label_map[label.color]
    return None


if __name__ == '__main__':  # pragma: no cover
    cli()
