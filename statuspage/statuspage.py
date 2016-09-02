# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

import sys, os
import hashlib
import base64
from datetime import datetime, timedelta
import requests
from requests.exceptions import ConnectionError
from github import Github, UnknownObjectException, GithubException
import click
from jinja2 import Template
from tqdm import tqdm
from collections import OrderedDict
import markdown2
import json

__version__ = "0.8.0"

try:
    ROOT = sys._MEIPASS
except AttributeError:
    ROOT = os.path.dirname(os.path.realpath(__file__))

PY3 = sys.version_info >= (3, 0)

COLORED_LABELS = (
    ("1192FC", "investigating",),
    ("FFA500", "degraded performance"),
    ("FF4D4D", "major outage", )
)

STATUSES = [status for _, status in COLORED_LABELS]

SYSTEM_LABEL_COLOR = "171717"

TEMPLATES = [
    "template.html",
    "style.css",
    "statuspage.js",
    "translations.ini"
]

DEFAULT_CONFIG = {
    "footer": "Status page hosted by GitHub, generated with <a href='https://github.com/jayfk/statuspage'>jayfk/statuspage</a>",
    "logo": "https://raw.githubusercontent.com/jayfk/statuspage/master/template/logo.png",
    "title": "Status",
    "favicon": "https://raw.githubusercontent.com/jayfk/statuspage/master/template/favicon.png"
}


@click.group()
@click.version_option(__version__, '-v', '--version')
def cli():  # pragma: no cover
    pass


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--token', prompt='GitHub API Token', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--systems', prompt='Systems, eg (Website,API)', help='')
@click.option('--private/--public', default=False)
def create(token, name, systems, org, private):
    run_create(name=name, token=token, systems=systems, org=org, private=private)


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--token', prompt='GitHub API Token', help='')
def update(name, token, org):
    run_update(name=name, token=token, org=org)


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--token', prompt='GitHub API Token', help='')
def upgrade(name, token, org):
    run_upgrade(name=name, token=token, org=org)


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--token', prompt='GitHub API Token', help='')
@click.option('--system', prompt='System', help='System to add')
@click.option('--prompt/--no-prompt', default=True)
def add_system(name, token, org, system, prompt):
    run_add_system(name=name, token=token, org=org, system=system, prompt=prompt)


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--token', prompt='GitHub API Token', help='')
@click.option('--system', prompt='System', help='System to remove')
@click.option('--prompt/--no-prompt', default=True)
def remove_system(name, token, org, system, prompt):
    run_remove_system(name=name, token=token, org=org, system=system, prompt=prompt)


@cli.command()
@click.option('--name', prompt='Name', help='')
@click.option('--org', help='GitHub Organization', default=False)
@click.option('--token', prompt='GitHub API Token', help='')
@click.option('--key', prompt='Key', help='', default=None)
def automate(name, token, org, key):
    run_automate(name=name, token=token, org=org, key=key)


def run_add_system(name, token, org, system, prompt):
    """
    Adds a new system to the repo.
    """
    repo = get_repo(token=token, org=org, name=name)
    try:
        repo.create_label(name=system.strip(), color=SYSTEM_LABEL_COLOR)
        click.secho("Successfully added new system {}".format(system), fg="green")
        if prompt and click.confirm("Run update to re-generate the page?"):
            run_update(name=name, token=token, org=org)
    except GithubException as e:
        if e.status == 422:
            click.secho(
                "Unable to add new system {}, it already exists.".format(system), fg="yellow")
            return
        raise


def run_remove_system(name, token, org, system, prompt):
    """
    Removes a system from the repo.
    """
    repo = get_repo(token=token, org=org, name=name)
    try:
        label = repo.get_label(name=system.strip())
        label.delete()
        click.secho("Successfully deleted {}".format(system), fg="green")
        if prompt and click.confirm("Run update to re-generate the page?"):
            run_update(name=name, token=token, org=org)
    except UnknownObjectException:
        click.secho("Unable to remove system {}, it does not exist.".format(system), fg="yellow")


def run_upgrade(name, token, org):
    click.echo("Upgrading...")

    repo = get_repo(token=token, name=name, org=org)
    files = get_files(repo=repo)
    head_sha = repo.get_git_ref("heads/gh-pages").object.sha

    # add all the template files to the gh-pages branch
    for template in tqdm(TEMPLATES, desc="Updating template files"):
        with open(os.path.join(ROOT, "template", template), "r") as f:
            content = f.read()
            if template in files:
                template_sha = repo.get_file_contents(
                    path="/" + template,
                    ref=head_sha,
                ).sha
                repo.update_file(
                    path="/" + template,
                    sha=template_sha,
                    message="upgrade",
                    content=content,
                    branch="gh-pages"
                )
            else:
                repo.create_file(
                    path="/" + template,
                    message="upgrade",
                    content=content,
                    branch="gh-pages"
                )


def run_update(name, token, org):
    click.echo("Generating..")
    repo = get_repo(token=token, name=name, org=org)
    issues = get_issues(repo)

    # get the SHA of the current HEAD
    sha = repo.get_git_ref("heads/gh-pages").object.sha

    # get the template from the repo
    template_file = repo.get_file_contents(
        path="/template.html",
        ref=sha
    )

    systems = get_systems(repo, issues)
    incidents = get_incidents(repo, issues)
    panels = get_panels(systems)

    # render the template
    config = get_config(repo)
    template = Template(template_file.decoded_content.decode("utf-8"))
    content = template.render({
        "systems": systems, "incidents": incidents, "panels": panels, "config": config
    })

    # create/update the index.html with the template
    try:
        # get the index.html file, we need the sha to update it
        index = repo.get_file_contents(
            path="/index.html",
            ref=sha,
        )

        if is_same_content(content, base64.b64decode(index.content)):
            click.echo("Local status matches remote status, no need to commit.")
            return False

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


def run_create(name, token, systems, org, private):
    gh = Github(token)

    if org:
        entity = gh.get_organization(org)
    else:
        entity = gh.get_user()

    # create the repo
    repo = entity.create_repo(name=name, private=private)

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

    click.echo("\nCreate new issues at https://github.com/{login}/{name}/issues".format(
        login=entity.login,
        name=name
    ))
    click.echo("Visit your new status page at https://{login}.github.io/{name}/".format(
        login=entity.login,
        name=name
    ))

    click.secho("\nYour status page is now set up and ready!\n", fg="green")
    click.echo("Please note: You need to run the 'statuspage update' command whenever you update or create an issue.\n")
    click.echo("There is a small service available ($39/year) that does that "
               "automatically for you.")
    if click.confirm("Set up automation?"):
        click.secho("\nAwesome!\n\n", fg="green")
        run_automate(name=name, token=token, org=org)
    else:
        click.echo("\nIn order to update this status page, run the following command:")
        click.echo("statuspage update --name={name} --token={token} {org}".format(
            name=name, token=token, org="--org=" + entity.login if org else ""))
        click.echo("")
        click.echo("In case you want to set up automation later, run:")
        click.echo("statuspage automate --name={name} --token={token} {org}".format(
            name=name, token=token, org="--org=" + entity.login if org else ""))


def run_automate(name, token, org, key=None):

    if not key:
        click.echo("If you don't have a key to use the backend service, go to "
                   "https://www.statuspage-backend.com to purchase one.\n")
        key = click.prompt('Key')

    data = {
        "name": name,
        "token": token,
        "org": org,
        "key": key
    }
    try:
        r = requests.post("https://www.statuspage-backend.com/register", json=data)
    except ConnectionError:
        click.secho("The backend server is not available. Please try again later.", fg="red")
        return
    try:
        data = r.json()
    except ValueError:
        click.secho("There was an error communicating with the backend server.", fg="red")
        return

    if not data.get("success", False):
        click.secho("Error: {}".format(data.get("error", "Unknown Error.")), fg="red")
        return

    click.secho("Automation activated.", fg="green")


def iter_systems(labels):
    for label in labels:
        if label.color == SYSTEM_LABEL_COLOR:
            yield label.name


def get_files(repo):
    """
    Get a list of all files.
    """
    return [file.path for file in repo.get_dir_contents("/", ref="gh-pages")]


def get_config(repo):
    """
    Get the config for the repo, merged with the default config. Returns the default config if
    no config file is found.
    """
    files = get_files(repo)
    config = DEFAULT_CONFIG
    if "config.json" in files:
        # get the config file, parse JSON and merge it with the default config
        config_file = repo.get_file_contents('/config.json', ref="gh-pages")
        try:
            repo_config = json.loads(config_file.decoded_content.decode("utf-8"))
            config.update(repo_config)
        except ValueError:
            click.secho("WARNING: Unable to parse config file. Using defaults.", fg="yellow")
    return config


def get_severity(labels):
    label_map = dict(COLORED_LABELS)
    for label in labels:
        if label.color in label_map:
            return label_map[label.color]
    return None


def get_panels(systems):
    # initialize and fill the panels with affected systems
    panels = OrderedDict()
    for system, data in systems.items():
        if data["status"] != "operational":
            if data["status"] in panels:
                panels[data["status"]].append(system)
            else:
                panels[data["status"]] = [system, ]
    return panels


def get_repo(token, name, org):
    gh = Github(token)
    if org:
        return gh.get_organization(org).get_repo(name=name)
    return gh.get_user().get_repo(name=name)


def get_collaborators(repo):
    return [col.login for col in repo.get_collaborators()]


def get_systems(repo, issues):
    systems = OrderedDict()
    # get all systems and mark them as operational
    for name in sorted(iter_systems(labels=repo.get_labels())):
        systems[name] = {
            "status": "operational",
        }

    for issue in issues:
        if issue.state == "open":
            labels = issue.get_labels()
            severity = get_severity(labels)
            affected_systems = list(iter_systems(labels))
            # shit is hitting the fan RIGHT NOW. Mark all affected systems
            for affected_system in affected_systems:
                systems[affected_system]["status"] = severity
    return systems


def get_incidents(repo, issues):
    # loop over all issues in the past 90 days to get current and past incidents
    incidents = []
    collaborators = get_collaborators(repo=repo)
    for issue in issues:
        labels = issue.get_labels()
        affected_systems = sorted(iter_systems(labels))
        severity = get_severity(labels)

        # make sure that non-labeled issues are not displayed
        if not affected_systems or severity is None:
            continue

        # make sure that the user that created the issue is a collaborator
        if issue.user.login not in collaborators:
            continue

        # create an incident
        incident = {
            "created": issue.created_at,
            "title": issue.title,
            "systems": affected_systems,
            "severity": severity,
            "closed": issue.state == "closed",
            "body": markdown2.markdown(issue.body),
            "updates": []
        }

        for comment in issue.get_comments():
            # add comments by collaborators only
            if comment.user.login in collaborators:
                incident["updates"].append({
                    "created": comment.created_at,
                    "body": markdown2.markdown(comment.body)
                })

        incidents.append(incident)

    # sort incidents by date
    return sorted(incidents, key=lambda i: i["created"], reverse=True)


def get_issues(repo):
    return repo.get_issues(state="all", since=datetime.now() - timedelta(days=90))


def is_same_content(c1, c2):
    def sha1(c):
        if PY3:
            if isinstance(c, str):
                c = bytes(c, "utf-8")
        else:
            c = c.encode()
        return hashlib.sha1(c)
    return sha1(c1).hexdigest() == sha1(c2).hexdigest()


if __name__ == '__main__':  # pragma: no cover
    cli()
