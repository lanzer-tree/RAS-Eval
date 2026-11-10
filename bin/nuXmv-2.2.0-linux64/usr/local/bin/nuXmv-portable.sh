#!/bin/sh -eu
# Self-contained nuXmv launcher: run the bundled x86-64 dynamic loader with the
# bundled libraries, independent of the host/container glibc. Works on native
# x86-64 Linux hosts and inside arm64 containers via Rosetta/qemu binfmt,
# without bind-mounting anything over /lib64.

rootdir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
libdir="$rootdir/lib/x86_64-linux-gnu"

exec "$libdir/ld-linux-x86-64.so.2" --library-path "$libdir" "$rootdir/bin/nuXmv" "$@"
