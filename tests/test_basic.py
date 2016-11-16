# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from pigeon import extract_crash_id


def test_basic(client):
    events = client.build_crash_save_events(client.crash_id_to_path('de1bb258-cbbf-4589-a673-34f800160918'))
    assert client.run(events) is None


def test_non_s3_event(client):
    events = {
        'Records': [
            {
                'eventSource': 'aws:lonnen',
            }
        ]
    }
    assert client.run(events) is None
    # FIXME: verify no rabbit message got created


def test_non_put_event(client):
    events = {
        'Records': [
            {
                'eventSource': 'aws:lonnen',
            }
        ]
    }
    assert client.run(events) is None
    # FIXME: verify no rabbit message got created


@pytest.mark.parametrize('data, expected', [
    # Raw crash file
    ('/v2/raw_crash/de1/20160918/de1bb258-cbbf-4589-a673-34f800160918', 'de1bb258-cbbf-4589-a673-34f800160918'),

    # Other files that get saved in the same bucket
    ('/v1/dump_names/de1bb258-cbbf-4589-a673-34f800160918', None),
    ('/v1/upload_file_minidump/de1bb258-cbbf-4589-a673-34f800160918', None),

    # Test-like files we might have pushed places to make sure things are working
    ('/v2/raw_crash/de1/20160918/test', None),
    ('/foo/bar/test', None),
])
def test_extract_crash_id(data, expected, client):
    record = client.build_crash_save_events(data)['Records'][0]
    assert extract_crash_id(record) == expected
