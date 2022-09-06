#!/bin/sh
#
# This file becomes the install section of the generated spec file.
#

# This is what dist.py normally does.
PYTHONDONTWRITEBYTECODE=1 python3 setup.py install --no-compile --prefix=/usr \
    --root=${RPM_BUILD_ROOT} --record="INSTALLED_FILES"

# Sort the filelist so that directories appear before files. This avoids
# duplicate filename problems on some systems.
touch DIRS
for i in $(cat INSTALLED_FILES)
do
    if [ -f ${RPM_BUILD_ROOT}/$i ]
    then
        echo $i >> FILES
    fi
    if [ -d ${RPM_BUILD_ROOT}/$i ]
    then
        echo %dir $i >> DIRS
    fi
done

# Make sure we match foo.pyo and foo.pyc along with foo.py (but only once each)
sed -e "/\.py[co]$/d" -e "s/\.py$/.py*/" DIRS FILES > INSTALLED_FILES

# Trick to emulate %config RPM macro
_CONFIG=( /etc/migasfree.conf )
for (( i = 0 ; i < ${#_CONFIG[@]} ; i++ ))
do
    _SED=${_CONFIG[$i]//\//\\/}
    sed -i -e "/^$_SED/d" INSTALLED_FILES
    echo %config ${_CONFIG[$i]} >> INSTALLED_FILES
done
