# Steps to perform an external release

## Prepare for internal release
- [ ] run full test suite locally, to make sure everything is fine
- [ ] perform ``Basic Feature Check`` (see #153)
- [ ] make sure documentation is updated

## Make internal release
- [ ] create release branch, checkout
- [ ] update ``NEWS.md``
- [ ] bump version in ``src/__init__.py``
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
- [ ] using the command line, cd to the ``src`` folder of your local development repo 
⇒ type ``python setup.py build``
- [ ] open ``build\exe.win32-3.7\TypeLoader.exe`` and perform a ``Basic Feature Check``
- [ ] using ``typeloader_installer_updater.py``, update the installer script. Scroll through the changes (compare old file with new side-by-side) and make sure they look good. Especially watch out for
  - header section still ok
  - consecutive ``SetOutPath`` statements (can happen if all files from a section were deleted) => manually delete all but the last of these in any given row
- [ ] using ``NIS Edit``, compile the installer by opening ``src/typeloader_installer_new.nsi`` and selecting „Compile and Run“ (Shift + F9)
- [ ] test the installer locally ⇒ make any necessary changes and commit them to the release branch
- [ ] using ``OwnCloud``, copy the installer to a ``Windows10`` computer outside the LSL-network.
- [ ] If it is not present already, install the previous version by using the old installer from the previous ``GitHub`` release.
- [ ] create a test login and perform a ``Basic Feature Check``
- [ ] With the new installer, update the existing version and perform a ``Basic Feature Check``. This should confirm that updating works as expected.
- [ ] Deinstall TypeLoader and remove the directory at TypeLoader's data-path, including all content. Then reinstall it with the the new installer, create a new test user and perform a ``Basic Feature Check``. This should confirm that the new version works for first-time users.
- [ ] If any changes need to be made, commit them to the release branch and copy it back to LSL. 
- [ ] Once everything works, run another test_suite and make sure everything is committed to the release branch. 

## Wrap up the new release
- [ ] Once users are happy, merge release branch back into ``master``
- [ ] merge ``master`` into ``productive``
- [ ] Tag the merge commit with the new version number
- [ ] push ``master`` to GitLab
- [ ] push ``productive`` to GitLab
- [ ] In the productive repo, pull from GitLab & checkout ``productive``
- [ ] If external release:
  - [ ] push ``productive`` to GitHub
  - [ ] create GitHub release including the new installer
  - [ ] announce the new release to the TypeLoader stakeholders
