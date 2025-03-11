echo "WARNING:"
echo "\tWe are in the process of deprecating shell script based tests. Please switch to calling this test via 'pytest -m \"extra\"'"

pytest -m "integration"