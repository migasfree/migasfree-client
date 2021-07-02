@echo off
cd ..

python setup.py bdist_wininst
python setup.py bdist
python setup.py bdist --format=msi

echo "Python requirements:"
echo "  * Python >= 3.6"
echo "  * python-magic-bin"
echo "  * pysam-win"
echo "  * pywin32"
echo "  * psutil"
echo "  * netifaces"
echo "  * jwcrypto"
echo "  * requests"
echo "  * requests-toolbelt"
echo "  * rich"
