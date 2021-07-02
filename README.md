Description
===========

'migasfree' is a very simple, but effective, systems management system. Actually, it is used in `Ayuntamiento de Zaragoza` (Spain) by initial authors in the project **migration to open source software for desktops**. They use [AZLinux distribution](http://zaragozaciudad.net/azlinux), which is based on [Ubuntu](http://www.ubuntu.com/).

You can learn about systems management systems at:

* [Systems management](http://en.wikipedia.org/wiki/Systems_management)
* [List of systems management systems](http://en.wikipedia.org/wiki/List_of_systems_management_systems)


License
=======

migasfree is free software, released under GNU GPL v3 (see LICENSE file for details).


Authors
=======

See AUTHORS file.


Requirements
============

* a Linux distribution (Fedora, openSUSE, Ubuntu, ...) or Windows 10
* Python >= 3.6 (see requirements.txt file)
* lshw >= B.02.15 (optional in Windows platform)
* dmidecode
* Extra requirements in Windows platform:
    * python-magic-bin
    * pysam-win
    * pywin32
    * psutil


Features (migasfree suite)
==========================

* Web administration
* Multiuser
* Multiversion (you can have desktops with differents versions and/or distributions of GNU/Linux)
* Automated Data Capture (you do not worry about adding hostnames, users, IPs, devices, etc. to server)
* Centralized system errors
* Centralized system faults
* Hardware inventory
* Software inventory
* System queries from the admin site


Behaviour
=========

How can you change the software configuration of machines with migasfree?

When an user opens a graphic session in the machine, migasfree client queries the migasfree Server and it responds with a code survey to execute in the client, created *ad hoc* for this client after consulting the database.

This code survey is executed in the client and basically configures the repositories of packages (rpm or deb). Previously, these repositories have been created for the server when the migasfree's administrator configures a repository.

A repository in migasfree server defines the packages that should be installed, updated or removed in the clients in function of attributes of client computer: **HOSTNAME**, **USER**, **LDAP CONTEXT**, **VIDEO CARD**, ... (the administrator defines the properties that he wants to use in his organization).

All changes of configuration in the clients are made through packages. Therefore it is necessary that you know how create packages in order to change the configuration of the machines that you want administrate. You can consider hiring a professional, this is the hard work, you were warned!


Use
===

For example: You want change the Firefox homepage in all PCs in a range of IPs.

1. You must create a package (for example `myorg-firefox-1-0.rpm` or `myorg-firefox_1-0.deb`). You must investigate which files need to be modified and allow the package to perform the task of changing the configuration. This is hard work!

2. You must upload your package to the server. This is simple!

3. You must create a repository in migasfree server. Add your package `myorg-firefox` and define the range of IPs. This is easy!

4. *Voilà!* When a user opens a graphic session and his IP is in range, migasfree client install the package.


Documentation
=============

[Fun with migasfree](http://fun-with-migasfree.readthedocs.org/) (spanish)


*That's all folks!!!*
