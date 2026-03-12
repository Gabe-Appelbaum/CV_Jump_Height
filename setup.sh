#!/bin/bash
# libgthread-2.0.so.0 was merged into libglib-2.0.so.0 in GLib 2.68+.
# MediaPipe still looks for the old shared-library name. Create a symlink.
LIBDIR="/usr/lib/x86_64-linux-gnu"
if [ ! -f "$LIBDIR/libgthread-2.0.so.0" ] && [ -f "$LIBDIR/libglib-2.0.so.0" ]; then
    sudo ln -sf "$LIBDIR/libglib-2.0.so.0" "$LIBDIR/libgthread-2.0.so.0"
fi
