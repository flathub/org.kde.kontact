#!/bin/bash
#
# Script to setup desktop and icon files to add another app (kmail, korganizer..) to the flatpak
#
# SPDX-FileCopyrightText: 2026 Noham Devillers <noham.devillers@enioka.com>
# SPDX-License-Identifier: GPL-2.0-or-later
#

function copy_app_desktop_file() {
  local src_desktop
  local dest_desktop

  src_desktop="${APPLICATIONS_DIR}/org.kde.${SRC_APP_NAME}.desktop"
  if [ -f "${src_desktop}" ]; then
      dest_desktop="${APPLICATIONS_DIR}/org.kde.kontact.${DEST_APP_NAME}.desktop"
      sed \
          -e "s|^Exec=.*|Exec=run_kontact.sh --${DEST_APP_NAME} %u|" \
          -e "s|^Icon=.*|Icon=org.kde.kontact.${DEST_APP_NAME}|" \
          "${src_desktop}" > "${dest_desktop}"
  fi
}

function copy_app_icon() {
    local icon_file="$1"
    local icon_dir
    local icon_ext
    local target_icon

    icon_dir="$(dirname "${icon_file}")"
    icon_ext="${icon_file##*.}"
    target_icon="${icon_dir}/org.kde.kontact.${DEST_APP_NAME}.${icon_ext}"

    cp "${icon_file}" "${target_icon}"
}

if [ -z "$1" ]; then
    echo "Usage: $0 <app_name>"
    exit 1
fi


# Some apps, are registered with other names (eg: kmail is registered as kmail2) so we have to have a different name for source and destination app too
SRC_APP_NAME="$1"
DEST_APP_NAME="$2"
APPLICATIONS_DIR="${APPLICATIONS_DIR:-/app/share/applications}"
ICONS_DIR="${ICONS_DIR:-/app/share/icons/hicolor}"

mkdir -p "${APPLICATIONS_DIR}"

copy_app_desktop_file

# Get icons files for the flatpak install
if [ -d "${ICONS_DIR}" ]; then
    find "${ICONS_DIR}" -name "${SRC_APP_NAME}.*" | while read -r icon_file; do
        copy_app_icon "${icon_file}"
    done
fi
