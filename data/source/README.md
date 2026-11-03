# Apple 2021 source snapshot

The compressed file contains the HTML DOM captured from the declared public SEC
filing on November 3, 2026:

https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm

SEC's [filing index](https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/0000320193-21-000105-index.htm)
identifies accession `0000320193-21-000105`, Apple Inc., Form 10-K, period ended
September 25, 2021, filed October 29, 2021.

Direct Python HTTP downloads returned 403. The canonical page was accessible in
the browser. Its complete DOM was serialized as UTF-8; the script element and
empty browser sidebar overlay were removed. Filing text, inline XBRL facts,
source anchor IDs and table structure were retained. Gzip uses a fixed mtime.
This is a **browser snapshot, not the original HTTP response bytes**. The
`raw_sha256` in the manifest identifies these saved snapshot bytes, not a
purported SEC-published hash. No third-party mirror was used.

The 174,200-byte archive permits deterministic offline setup without depending
on a teammate's SEC download access. `scripts/parse_filing.py` verifies the
archive and decompressed checksum, checks filing identity, and restores the
ignored `data/raw/aapl-20210925.browser.html` when absent. Do not overwrite that
file with a separately downloaded representation and bypass the checksum.

To review a future source refresh, save it separately, check the accession and
source facts, explicitly update the manifest/archive and rerun all parser tests.
Changing source representation can change CSS locators and evidence IDs; it
therefore requires a filing-specific index rebuild by the index owner.
