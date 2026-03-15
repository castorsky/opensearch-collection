#!/usr/bin/env bash
# Copyright (c) Castor Sky (@castorsky) <csky57@gmail.com>
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

set -eux

ansible-playbook module_test.yml -i "./inventory.yml" "$@"
