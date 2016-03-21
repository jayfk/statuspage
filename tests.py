# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest
from datetime import datetime
from unittest import TestCase
from mock import patch, Mock
from click.testing import CliRunner
from statuspage import cli, create, upgrade
from github import UnknownObjectException


class CLITestCase(TestCase):

    def setUp(self):
        self.patcher = patch('statuspage.Github')
        self.gh = self.patcher.start()

        # setup mocked label
        self.label = Mock()
        self.label.color = "171717"
        self.label.name = "Website"

        self.label1 = Mock()
        self.label1.color = "171717"
        self.label1.name = "API"

        self.gh().get_user().get_repo().get_labels.return_value = [self.label, self.label1]

        # set up mocked issue
        self.issue = Mock()
        self.issue.created_at = datetime.now()
        self.issue.state = "open"
        self.issue_label = Mock()
        self.issue_label.color = "FF4D4D"
        self.issue_label.name = "major outage"
        self.issue.get_labels.return_value = [self.issue_label, self.label]
        self.issue.user.login = "some-dude"
        self.comment = Mock()
        self.comment.user.login = "some-dude"
        self.issue.get_comments.return_value = [self.comment, ]

        self.issue1 = Mock()
        self.issue1.created_at = datetime.now()
        self.issue1.state = "open"
        self.issue1.user.login = "some-dude"
        self.issue1.get_labels.return_value = [self.issue_label, self.label1]
        self.issue1.get_comments.return_value = [self.comment, ]

        self.gh().get_user().get_repo().get_issues.return_value = [self.issue, self.issue1]
        self.template = Mock()
        self.template.decoded_content = b"some foo"
        self.gh().get_user().get_repo().get_file_contents.return_value = self.template
        self.gh().get_organization().get_repo().get_file_contents.return_value = self.template

        self.collaborator = Mock()
        self.collaborator.login = "some-dude"

        self.gh().get_user().get_repo().get_collaborators.return_value = [self.collaborator,]
        self.gh().get_organization().get_repo().get_collaborators.return_value = [self.collaborator,]

    def tearDown(self):

        self.patcher.stop()

    def test_create(self):

        label = Mock()
        self.gh().get_user().create_repo().get_labels.return_value = [label,]

        runner = CliRunner()
        result = runner.invoke(
                create,
                ["--name", "testrepo", "--token", "token", "--systems", "sys1,sys2"]
        )
        self.assertEqual(result.exit_code, 0)

        self.gh.assert_called_with("token")

    def test_create_org_no_collabs(self):

        runner = CliRunner()
        result = runner.invoke(
                create,
                ["--name", "testrepo",
                 "--token", "token",
                 "--systems", "sys1,sys2",
                 "--org", "some"]
        )

        self.assertEqual(result.exit_code, -1)

        self.gh.assert_called_with("token")
        self.gh().get_organization.assert_called_with("some")

    def test_create_org(self):
        member = Mock()
        member.login = "some-user"
        self.gh().get_organization("some").get_members.return_value = [member,]

        runner = CliRunner()
        result = runner.invoke(
                create,
                ["--name", "testrepo",
                 "--token", "token",
                 "--systems", "sys1,sys2",
                 "--org", "some"]
        )

        self.assertEqual(result.exit_code, 0)

        self.gh.assert_called_with("token")
        self.gh().get_organization.assert_called_with("some")

    def test_run_upgrade(self):

        runner = CliRunner()
        result = runner.invoke(
                upgrade,
                ["--name", "testrepo",
                 "--token", "token"]
        )

        self.assertEqual(result.exit_code, 0)
        self.gh.assert_called_with("token")



if __name__ == '__main__':
    unittest.main()