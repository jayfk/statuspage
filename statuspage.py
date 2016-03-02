# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
from github import Github
import click
from jinja2 import Template
from tqdm import tqdm
from datetime import datetime, timedelta

__version__ = "0.1"

COLORED_LABELS = (
    ("1192FC", "investigating",),
    ("FFA500", "degraded performance"),
    ("FF4D4D", "major outage", )
)

STATUSES = [status for _, status in COLORED_LABELS]

SYSTEM_LABEL_COLOR = "171717"

TEMPLATES = [
    #"favicon.png",
    "template.html",
    #"logo.png",
    "milligram.min.css",
    #"README.md",
    "style.css"
]

@click.group()
@click.version_option(__version__, '-v', '--version')
def cli():  # pragma: no cover
    pass

@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--token', prompt='GitHub API Token', help='')
@click.option('--systems', prompt='Systems, eg (Website,API)', help='')
def create(token, name, systems):
    gh = Github(token)
    user = gh.get_user()
    delete = user.get_repo(name)
    delete.delete()

    # create the repo
    repo = user.create_repo(name=name)

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
        path="/index.html",
        message="noting here, move on",
        content="",
    )

    # create the gh-pages branch
    ref = repo.get_git_ref("heads/master")
    repo.create_git_ref(ref="refs/heads/gh-pages", sha=ref.object.sha)

    # add all the template files to the gh-pages branch
    for template in tqdm(TEMPLATES, desc="Adding template files"):
        with open("template/" + template, "r") as f:
            repo.create_file(
                path="/" + template,
                message="initial",
                content=f.read(),
                branch="gh-pages"
            )

    # set the gh-pages branch to be the default branch
    repo.edit(name=name, default_branch="gh-pages")
    # run an initial update to add content to the index
    update(token=token, name=name)

    click.echo("Create new issues at https://github.com/{login}/{name}/issues".format(
        login=user.login,
        name=name
    ))
    click.echo("Visit your new status page at https://{login}.github.io/{name}/".format(
        login=user.login,
        name=name
    ))


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--token', prompt='GitHub API Token', help='')
def update(name, token):
    gh = Github(token)
    repo = gh.get_user().get_repo(name=name)
    systems, incidents = {}, []

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
            incident["updates"].append({
                "created": comment.created_at,
                "body": comment.body
            })

        incidents.append(incident)

    # sort incidents by date
    incidents = sorted(incidents, key=lambda i: i["created"], reverse=True)

    # initialize and fill the panels with affected systems
    panels = dict([(status, []) for status in STATUSES])
    for system, data in systems.items():
        if data["status"] != "operational":
            panels[data["status"]].append(system)

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