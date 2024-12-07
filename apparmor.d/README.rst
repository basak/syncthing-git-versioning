Syncthing Apparmor Profiles
===========================

Security-sensitive advanced users may wish to run Syncthing under AppArmor
confinement. Here are the profiles I use (thanks to
https://github.com/krathalan). You will most likely need to modify them to
point to your installation location and sync folders.

Using the syncthing-git-versioning hook needs additional AppArmor rules as
might be expected. On Debian, the systemd service ships with
``NoNewPrivileges=true`` so using a separate profile for the hook won't work.
On balance, it seemed to me that the ``NoNewPrivileges`` restriction is
preferable, so I implemented the extra rules inside
``/etc/apparmor.d/local/usr.bin.syncthing`` directly.
