# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest
from datetime import datetime
from unittest import TestCase
from mock import patch, Mock
from click.testing import CliRunner
from statuspage import cli, update, create, iter_systems, get_severity, SYSTEM_LABEL_COLOR
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

    @patch("statuspage.run_update")
    def test_create(self, run_update):

        label = Mock()
        self.gh().get_user().create_repo().get_labels.return_value = [label,]

        runner = CliRunner()
        result = runner.invoke(
                create,
                ["--name", "testrepo", "--token", "token", "--systems", "sys1,sys2"]
        )

        self.assertEqual(result.exit_code, 0)

        self.gh.assert_called_with("token")

    @patch("statuspage.run_update")
    def test_create_org(self, run_update):

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

    def test_update(self):

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token"])

        self.assertEqual(result.exit_code, 0)

        self.gh.assert_called_with("token")

        self.gh().get_user().get_repo.assert_called_with(name="testrepo")
        self.gh().get_user().get_repo().get_labels.assert_called_once_with()

    def test_update_org(self):

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token", "--org", "some"])

        self.assertEqual(result.exit_code, 0)

        self.gh.assert_called_with("token")

        self.gh().get_organization().get_repo.assert_called_with(name="testrepo")
        self.gh().get_organization().get_repo().get_labels.assert_called_once_with()

    def test_update_index_does_not_exist(self):

        self.gh().get_user().get_repo().update_file.side_effect = UnknownObjectException(status=404, data="foo")

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token"])
        self.assertEqual(result.exit_code, 0)

        self.gh.assert_called_with("token")

        self.gh().get_user().get_repo.assert_called_with(name="testrepo")
        self.gh().get_user().get_repo().get_labels.assert_called_once_with()
        self.gh().get_user().get_repo().create_file.assert_called_once_with(
            branch='gh-pages',
            content='some foo',
            message='initial',
            path='/index.html'
        )

    def test_update_non_labeled_issue_not_displayed(self):
        self.issue.get_labels.return_value = []

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token"])
        self.assertEqual(result.exit_code, 0)

        # make sure that get_comments is not called for the first issue but for the second
        self.issue.get_comments.assert_not_called()
        self.issue1.get_comments.assert_called_once_with()

    def test_update_non_colaborator_issue_not_displayed(self):
        self.issue.user.login = "some-other-dude"

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token"])
        self.assertEqual(result.exit_code, 0)

        # make sure that get_comments is not called for the first issue but for the second
        self.issue.get_comments.assert_not_called()
        self.issue1.get_comments.assert_called_once_with()


class UtilTestCase(TestCase):

    def test_iter_systems(self):
        label1 = Mock()
        label2 = Mock()
        label1.name = "website"
        label1.color = SYSTEM_LABEL_COLOR

        self.assertEqual(
            list(iter_systems([label1, label2])),
            ["website", ]
        )

        self.assertEqual(
            list(iter_systems([label2])),
            []
        )

    def test_severity(self):
        label1 = Mock()
        label2 = Mock()
        label1.color = "FF4D4D"

        self.assertEqual(
            get_severity([label1, label2]),
            "major outage"
        )

        label1.color = "000000"

        self.assertEqual(
            get_severity([label1, label2]),
            None
        )




if __name__ == '__main__':
    unittest.main()