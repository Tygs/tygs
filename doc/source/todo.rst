TODO
====

- Document C accelerators (cchardet, ujson, jinja2)
- Add a CHANGES file
- integrate changes from https://github.com/tweepy/tweepy/blob/master/setup.py
- add a tox env avoiding print() and pdb.set_trace
- Move signal dispatcher to put it on the project object
- Move signal dispatcher to its own projet.
- Create subprojects holding code for tygs. Should we call them tygseed ?
  We could have tygseed-dispatch, tygseed-aioutils, etc. Or even tygseed.dispatch
  if it's allowed.
- Document lifecycle and events
- Use prb for packaging
- Use bandit for vulnerabilities
- Use the big list of nauthy strings to test for vulnerabilities
- One-commnd deploy
- Exception page with a lot of tools inside (search to stackoverflow, pdb shell, link to doc, etc)
- Official contrib pages including : git commit policy, list of easy bug pick, tutorials to get started, general schema of internals
