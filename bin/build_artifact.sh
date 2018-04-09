#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Builds a deploy artifact of what got deployed.
#
# Usage: bin/build_artifact.sh

SHA1="$(git rev-parse HEAD)"
TAG=""
PROJECT_REMOTE="https://github.com/$(git remote | head -n 1 | xargs git remote get-url | sed -E 's/[^:]*:(.*)\..*$/\1/')"
BUILD="${PIGEON_BUILD_ID:=nobuild}"

printf '{"commit":"%s","version":"%s","source":"%s","build":"%s"}\n' "$SHA1" "$TAG" "$PROJECT_REMOTE" "$BUILD" > version.json
