#!/bin/bash
#
# Kontact/Akonadi launch script
#
# SPDX-FileCopyrightTexti: 2020 Daniel Vrátil <dvratil@kde.org>
# SPFX-License-Identifier: GPL-2.0-or-later
#

function stop_akonadi {
    akonadictl stop
    count=0
    while akonadictl status 2>&1 | grep -q "running" && [ ${count} -lt 5 ]; do
        echo "Waiting for Akonadi to stop..."
        ((count=count+1))
        sleep 1
    done
}

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
else
    # If we are using the default instance, make sure we are running
    # against the Flatpak instance, not the system-wide one
    stop_akonadi
fi

# Kontact requires that ksycoca cache exists, but cannot run kbuildsycoca6
# automatically (because KDED lives outside of the sandbox).
# As a workaround we force-run it ourselves. It's really only needed once,
# but detecting whether it already exists or not is hard and the overhead
# is minimal.
kbuildsycoca6

# Default binary to execute
APP_BIN="kontact"

# Check first argument for custom target binary
case "$1" in
    --kmail)
        APP_BIN="kmail"
        shift
        ;;
    --korganizer)
        APP_BIN="korganizer"
        shift
        ;;
    --kaddressbook)
        APP_BIN="kaddressbook"
        shift
        ;;
esac

# Execute the chosen application, forwarding all remaining arguments
exec "$APP_BIN" "$@"

