#!/usr/bin/env bash

max_line_length=120
declare -a cmds=(
    "autopep8 --aggressive --aggressive --max-line-length=${max_line_length}"
    "flake8 --max-line-length=${max_line_length}"
    "bandit"
    "pylint --max-line-length=120 --msg-template='{path} : {msg_id} {line:3d},{column}: {obj}: {msg} ({symbol})'"
    "pydocstyle --convention=numpy"
)
files=`find . -name '*.py'`

for file in ${files[@]}; do
    printf "\n====================\n%s\n====================\n" "$file"
    for cmd in "${cmds[@]}"; do
        printf "\n--------------------\n%s\n%s\n--------------------\n" "$file" "$cmd"
        eval $cmd $file
    done
done
