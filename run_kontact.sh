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
fi

# Make sure we run against our own Akonadi instance
stop_akonadi

# Make sure that our Akonadi is stopped when this script exits, as there
# is no way to shut it down later and it would interfere with the next run.
trap stop_akonadi EXIT TERM

# Kontact requires that ksycoca cache exists, but cannot run kbuildsycoca5
# automatically (because KDED lives outside of the sandbox).
# As a workaround we force-run it ourselves. It's really only needed once,
# but detecting whether it already exists or not is hard and the overhead
# is minimal.
kbuildsycoca5

# fire up Akonadi
akonadictl start

# .. aaaaand lift-off
exec kontact "$@"


