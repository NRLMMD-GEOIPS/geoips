# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

echo "WARNING:"
echo "\tWe are in the process of deprecating shell script based tests. Please switch to calling this test via 'pytest -m \"extra\"'"

pytest -m "integration"