#!/bin/bash
#
# Kontact/Akonadi launch script
#
# SPDX-FileCopyrightTexti: 2020 Daniel Vrátil <dvratil@kde.org>
# SPFX-License-Identifier: GPL-2.0-or-later
#

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"

# We want to use a dedicated Akonadi instance in the Flatpak in order
# to avoid the exported DBus names to conflict with the default
# non-flatpak Akonadi.
# However, we did not do this from the very beginning of this Flatpak,
# so we can only use the dedicated instance if the default instance
# configuration doesn't exist, or in other words if the user ran
# this Flatpak for the first time after this feature has been introduced.
# There is no possible migration path from the default instance to the
# dedicated instance for existing users.
if [ ! -f "${XDG_CONFIG_HOME}/akonadi/akonadiserverrc" ]; then
    export AKONADI_INSTANCE="flatpak"
elif serverpath="$(dbus-send --session --dest=org.freedesktop.Akonadi \
    --type=method_call --print-reply=literal /Server \
    org.freedesktop.Akonadi.Server.serverPath)"; then
    # If we are using the default instance, make sure we are running
    # against the Flatpak instance, not the system-wide one
    case "$serverpath" in
    */org.kde.kontact/*)
        # System akonadi does not have application ID in the path.
        ;;
    *)
        akonadictl stop --wait
        ;;
    esac
fi

# Kontact requires that ksycoca cache exists, but cannot run kbuildsycoca6
# automatically (because KDED lives outside of the sandbox).
# As a workaround we force-run it ourselves. It's really only needed once,
# but detecting whether it already exists or not is hard and the overhead
# is minimal.
kbuildsycoca6

# Start requested application, this will auto-start Akonadi if needed.
if [ "$#" -eq 0 ]; then
    exec kontact
else
    exec "$@"
fi
