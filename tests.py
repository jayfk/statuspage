# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import unittest
from unittest import TestCase
from mock import patch, Mock
from click.testing import CliRunner
from statuspage import cli, update, create, iter_systems, get_severity, SYSTEM_LABEL_COLOR


class CLITestCase(TestCase):

    @patch("statuspage.Github")
    def test_create(self, GithubMock):

        gh = Mock()
        GithubMock.return_value = gh

        label = Mock()
        gh.get_user().create_repo().get_labels.return_value = [label,]

        runner = CliRunner()
        result = runner.invoke(
                create,
                ["--name", "testrepo", "--token", "token", "--systems", "sys1,sys2"]
        )

        self.assertEqual(result.exit_code, 0)

        GithubMock.assert_called_once_with("token")


    @patch("statuspage.Github")
    def test_update(self, GithubMock):

        gh = Mock()
        GithubMock.return_value = gh

        # setup mocked label
        label = Mock()
        label.color = "171717"
        label.name = "Website"
        gh.get_user().get_repo().get_labels.return_value = [label, ]

        # set up mocked issue
        issue = Mock()
        issue.state = "open"
        issue_label = Mock()
        issue_label.color = "FF4D4D"
        issue_label.name = "major outage"
        issue.get_labels.return_value = [issue_label, label]
        comment = Mock()
        issue.get_comments.return_value = [comment, ]
        gh.get_user().get_repo().get_issues.return_value = [issue, ]

        runner = CliRunner()
        result = runner.invoke(update, ["--name", "testrepo", "--token", "token"])

        self.assertEqual(result.exit_code, 0)

        GithubMock.assert_called_with("token")

        gh.get_user().get_repo.assert_called_with(name="testrepo")
        gh.get_user().get_repo().get_labels.assert_called_once_with()


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