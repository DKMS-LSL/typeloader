# Steps to perform a TypeLoader release

## Prepare for internal release
- [ ] run full test suite locally, to make sure everything is fine
- [ ] perform `Basic Feature Check`
  - [ ] Start TypeLoader
  - [ ] Log in (**use a TEST user!**)
  - [ ] Create a project
  - [ ] Upload all example sequence
  - [ ] Submit test sequence to ENA (test server!)
  - [ ] Using the example pretypings- and ENA reply-files, create IPD submission files for all test sequences
  - [ ] Click through each view to make sure they are fine.
- [ ] make sure documentation is updated
- [ ] draft test plan
- [ ] let process owner approve test plan

## Make internal release
- [ ] create release branch, checkout
- [ ] update ``NEWS.md``
- [ ] bump version to **release cadidate** in ``typeloader2/__init__.py`` 
- [ ] bump version to **release cadidate** in ``pyproject.toml``
- [ ] commit everything
- [ ] push release branch to ``GitLab``
- [ ] create merge request
- [ ] approve & squash-merge merge request
- [ ] pull to stage repo (``T:\Skripte\_STAGE_\typeloader2``)
- [ ] attach test log to release ticket
- [ ] announce stage release & request testing
- [ ] testing by process owner
- [ ] if necessary, make adjustments, abort release candidate & create new release ticket

## Optionally: Make external release
- [ ] update the version number in ``setup.py``
- [ ] update NEW_VERSION in ``typeloader_installer_updater.py``, then run it
- [ ] test the installer locally ⇒ make any necessary changes and commit them to the release branch
- [ ] using ``FTApi``, copy the installer to a ``Windows10`` computer outside the LSL-network.
- [ ] if it is not present already, install the previous version by using the old installer from the previous ``GitHub`` release.
- [ ] create a test login and perform a ``Basic Feature Check``
- [ ] with the new installer, update the existing version and perform a ``Basic Feature Check``. This should confirm that updating works as expected.
- [ ] deinstall TypeLoader and check whether any files remain behind. If so, use ``deinstaller_cleanup.py`` to adjust the installer accordingly. Then recreate the installer from the adjusted script.
- [ ] remove the directory at TypeLoader's data-path, including all content. Then reinstall it with the the new installer, create a new test user and perform a ``Basic Feature Check``. This should confirm that the new version works for first-time users.
- [ ] if any changes need to be made, commit them to the release branch and copy it back to LSL.
- [ ] once everything works, run another test_suite and make sure everything is committed to the release branch.
- [ ] squash-merge the release branch into master using a merge request
- [ ] move the new installer from ``typeloader2`` to ``installer\windows``.

/label ~todo ~release
