#!/bin/sh
#
# This file becomes the install section of the generated spec file.
#

%define _unpackaged_files_terminate_build 0

# This is what dist.py normally does.
python3 setup.py install --prefix=/usr --root="${RPM_BUILD_ROOT}" --record="INSTALLED_FILES" \
--install-lib="$(python3 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")"

# Sort the filelist so that directories appear before files. This avoids
# duplicate filename problems on some systems.
touch DIRS
for i in $(cat INSTALLED_FILES)
do
    if [ -f "${RPM_BUILD_ROOT}/$i" ]
    then
        echo "$i" >> FILES
    fi
    if [ -d "${RPM_BUILD_ROOT}/$i" ]
    then
        echo %dir "$i" >> DIRS
    fi
done

# Make sure we match foo.pyo and foo.pyc along with foo.py (but only once each)
sed -e "/\.py[co]$/d" -e "s/\.py$/.py*/" DIRS FILES > INSTALLED_FILES
