ROOT=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
rpmbuild --define "_topdir $ROOT" -ba $ROOT/SPECS/ftp2http.spec
