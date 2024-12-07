syncthing-git-versioning
========================

.. A single sentence that says what the product is, succinctly and memorably

syncthing-git-versioning is an external versioning hook for `Syncthing`_ that
saves old versions of files into a git repository.

.. A paragraph of one to three short sentences, that describe what the product
   does.

When Syncthing synchronises a change to a file that requires the local file to
be modified or deleted, then in addition to internal versioning options, it can
be configured to call an external versioning hook. This tool is such a hook. It
will move the file into a git repository and commit it. By setting up a synced
folder that uses this hook, you can keep old versions of such files. If you use
`git-annex`_, then the file contents can be separated from their metadata, and
old file contents can also be selectively deleted later to recover their space.

.. A third paragraph of similar length, this time explaining what need the
   product meets.

This is useful for Syncthing users to keep old file versions around in an
organised way. Old data is separated from the sync folder itself, so
misbehaviour on a different node cannot lost data on your node. Note however
that it isn't a substitute for a backup system. Since Syncthing only calls the
hook when a file is to be modified, it isn't possible to roll back to a
snapshot at a given time. Nor is it possible prune old files according to their
age, since their ages cannot be known to the hook.

.. Finally, a paragraph that describes whom the product is useful for.

This tool is useful for any Syncthing user. It uses Linux tools so isn't
suitable for use on Windows, but if you add a Linux node running this
versioning script, then your old files can be stored there.

Quick Start
-----------

#. Download ``syncthing-file-versioning`` to ``/usr/local/bin/`` and mark it
   executable using ``chmod 755 /usr/local/bin/syncthing-file-versioning`` (or
   use some other path as you wish).

#. Create a git repository to correspond to a sync folder (create the
   directory, then run ``git init``).

#. In Syncthing, go to "Edit" against your desired folder and go to the "File
   Versioning" tab. Under "File Versioning", choose "External File Versioning"
   and set "Command" to ``syncthing-git-versioning /path/to/repo
   %FOLDER_PATH% %FILE_PATH%``, replacing
   ``/path/to/repo`` with the path the git repository you created in the
   previous step. Do not expand ``%FOLDER_PATH%`` nor ``%FILE_PATH%``;
   Syncthing will do this at runtime.

#. Test by changing and deleting files in the sync folder on other devices.
   After Syncthing has synced the changes, inspect the git repository. You
   should see old versions of changed and deleting files appearing there.

Details
-------

* The only dependencies are git itself, ``/bin/sh`` and common shell tools. You
  can generally expect all of these to be available as part of any modern Linux
  base system.

* You may want the git repository to reflect the current state of the synced
  folder as well as containing previous versions. However, this tool doesn't do
  that, since Syncthing's external versioning mechanism is only called when a
  file is modified or deleted, not when it is first created. In this sense, the
  git repository only operates "retrospectively". In the case that files are
  always uniquely named and never modified, the git repository can be expected
  to be empty, since in this case no old versions of files exist.

* To use `git-annex`_, just use ``git annex init`` as normal. This tool will
  automatically detect that an annex is present, and use ``git annex add``
  instead of plain ``git add``. For finer control of what gets added to the
  annex, you can configure ``annex.largefiles`` directly. See
  `git-annex-config(1)`_ for details.

* If a file changes to a directory or vice versa, then inserting them into a git
  repository can get complicated. This tool is intended to handle all of this
  for you.

* If you use AppArmor to confine syncthing (this isn't the default), then you
  will need to add rules to allow this tool to do its work. See the
  ``apparmor/`` directory for an example.

* A test suite is included. On Debian, you can run this with ``py.test-3``
  after ``sudo apt install git git-annex python3-pytest``. The test suite uses
  the ``syncthing-git-versioning`` shell script that is in the same directory
  as the test suite itself.

License
-------

This tool and associated files are subject to the terms of the Mozilla Public
License, v. 2.0. A copy of the license is include the file ``LICENSE`` in the
source repository, or you can obtain it from https://mozilla.org/MPL/2.0/.

.. _Syncthing: https://syncthing.net/
.. _git-annex: https://git-annex.branchable.com/
.. _git-annex-config(1): https://git-annex.branchable.com/git-annex-config/
