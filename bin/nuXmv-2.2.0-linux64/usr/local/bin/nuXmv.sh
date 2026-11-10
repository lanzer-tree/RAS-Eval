#!/bin/sh -eu

quit() {
    echo "$0: ${1:-error}" >&2
    exit 1
}

# assuming bin/ and lib/ are siblings
rootdir=$(realpath $(dirname "$0")/..)
test -d "$rootdir" || quit "rootdir not found"
#
# libnuxmv may be further below lib/
libnuxmv=$(find $rootdir -name 'libnuxmv.*')
test -e "$libnuxmv" || quit "libnuxmv not found"

libdir=$(dirname $libnuxmv)
test -d "$libdir" || quit "libdir not found"

case "$(uname -s)" in
    Darwin)
        export DYLD_LIBRARY_PATH="${DYLD_LIBRARY_PATH:+$DYLD_LIBRARY_PATH:}$libdir"
        ;;
    Linux)
        export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:+$LD_LIBRARY_PATH:}$libdir"
        ;;
esac

exec "$rootdir/bin/nuXmv" "$@"
