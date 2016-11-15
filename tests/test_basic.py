# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

def test_basic(client):
    events = client.build_crash_save_events(['de1bb258-cbbf-4589-a673-34f800160918'])
    assert client.run(events) is None
