# Steps to perform a TypeLoader deployment / change

- [ ] draft test plan
- [ ] let process owner approve test plan
- [ ] negotiate time window with process owner
- [ ] create change branch
- [ ] bump version to **release cadidate** in ``typeloader2/__init__.py``
- [ ] bump version to **release cadidate** in ``pyproject.toml``
- [ ] push to GitLab (``--follow-tags``)
- [ ] squash-merge using a merge request
- [ ] tag the merge commit with the new version number
- [ ] in productive repo (``T:\Skripte\TypeLoader2``), pull master
- [ ] write an email to all TypeLoader stakeholders (.forschung and .bioinf) announcing the new release, including all important changes to the last version (use ``NEWS.md`` as a guideline)

- [ ] if external release:
  - [ ] push ``master`` to GitHub
  - [ ] create ``GitHub`` release including the new installer

- [ ] delete merged branches from DEV 

/label ~todo ~release
