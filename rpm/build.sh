#!/bin/env bash

test $1 && {
    VERSION=$1
}|| {
    echo "The VERSION must be supplied as an argument."
    exit 1
}

ROOT=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)

rpmbuild --define "version $VERSION" --define "_topdir $ROOT" -ba $ROOT/SPECS/ftp2http.spec
