# Change Log
All enhancements and patches to statuspage will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## 0.8.1 [2016-09-6]
- Fixed a silly encoding error on legacy python

## 0.8.0 [2016-09-2]
- Added client side translation.
- Added german translation.
- It's now possible to add/remove systems from the CLI.

## 0.7.0 [2016-07-31]
- Added markdown support.
- Added upgrade command.
- Added support for localtime.
- Added support for a config file.

## 0.6.0 [2016-07-26]
- Added an option to automate the update process.
- Switch to PyGithub as pygithub-redux is no longer needed
- Added an option to create private repositories
- Beefed up the docs

## 0.5.1 [2016-07-26]
- Updated dependencies: tqdm and pygithub-redux

## 0.5.0 [2016-07-26]
- Systems and Panels are now ordered to make sure that no commit is issued when nothing changes (#12)
- Refactored the code to make it easier to read

## 0.4.1 [2016-07-25]
- Fixed a bug on python 3 where the hash function wasn't working.

## 0.4.0 [2016-07-25]
- Only commit if content differs (@Jcpetrucci)

## 0.3.3 [2016-07-13]
- issued new pypi release

## 0.3.2 [2016-07-13]
- fixed packaging problems by using a module
- minified and merged style.css with milligram.min.css

## 0.3.1 [2016-07-12]
- fixed packaging problems

## 0.3 [2016-07-12]
- statuspage is now available on PyPi

## 0.2 [2016-03-08]
- Added support for GitHub organizations
- Makes sure that non-collaborator issues/comments are not displayed

## 0.1 [2016-03-07]
- Initial release
