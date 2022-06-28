# Steps to perform an external release

## Prepare for internal release
- [ ] run full test suite locally, to make sure everything is fine
- [ ] perform ``Basic Feature Check`` (see #153)
- [ ] make sure documentation is updated

## Make internal release
- [ ] create release branch, checkout
- [ ] update ``NEWS.md``
- [ ] bump version in ``typeloader2/__init__.py``
- [ ] commit everything
- [ ] push release branch to ``GitLab``
- [ ] in productive repo (``T:\Skripte\TypeLoader2``), pull from ``GitLab`` and checkout release branch
- [ ] using the ``test`` user, perform ``Basic Feature Check``
- [ ] write an email to all TypeLoader stakeholders (.forschung and .bioinf) announcing the new release, including all important changes to the last version (use ``NEWS.md`` as a guideline)
- [ ] wait a few days for feedback
- [ ] if necessary, make adjustments and commit them to the release branch. If any change to functionality, bump version number & notify users.

## Optionally: Make external release
- [ ] checkout the release branch in your local development repo
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
- [ ] move the new installer from ``typeloader2`` to ``installer\windows``.

## Wrap up the new release
- [ ] Once users are happy, merge release branch back into ``master`` (``--no-ff``)
- [ ] merge ``master`` into ``productive`` (``--no-ff``)
- [ ] merge productive back into master to get all heads to the same commit (fast-forward is fine, so **don't use --no-ff** or you will get another merge commit!)
- [ ] tag the merge commit on ``productive`` with the new version number
- [ ] push ``master`` to GitLab
- [ ] push ``productive`` to GitLab
- [ ] In the productive repo, pull from GitLab & checkout ``productive``
- [ ] If external release:
  - [ ] push ``master`` and ``productive`` to GitHub
  - [ ] create ``GitHub`` release including the new installer
  - [ ] announce the new release to the TypeLoader stakeholders
- [ ] Delete release branch
  - [ ] from ``GitLab``
  - [ ] from productive repo
  - [ ] from local development repo

/label ~todo ~release
