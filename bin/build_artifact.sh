#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Builds a deploy artifact of what got deployed.
#
# Usage: bin/build_artifact.sh
#
# Set these vars in the environment:
#
#   PIGEON_BUILD_ID: the build id
#   PIGEON_SOURCE: the source url

SHA1="$(git rev-parse HEAD)"
TAG=""
SOURCE="${PIGEON_SOURCE}"
BUILD="${PIGEON_BUILD_ID:=nobuild}"

printf '{"commit":"%s","version":"%s","source":"%s","build":"%s"}\n' "$SHA1" "$TAG" "$SOURCE" "$BUILD" > version.json
