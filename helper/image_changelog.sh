#!/bin/bash

version=$(poetry run helper/update_version.py $1)

for changelog in $(find image -name "*Migration.changes"); do
    pushd $(dirname "${changelog}")
    osc vc -m "Bump version: ${version}"
    popd
done

git commit -S -a -m "Bump Migration changelog version: ${version}"
