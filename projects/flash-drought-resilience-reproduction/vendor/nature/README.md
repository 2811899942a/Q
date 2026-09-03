# Nature official assets

Target location for official publisher assets after they are downloaded and redistribution rights are checked.

Expected filenames:

- `41467_2026_70417_MOESM1_ESM.pdf` - Supplementary Information
- `41467_2026_70417_MOESM2_ESM.pdf` - Reporting Summary
- `41467_2026_70417_MOESM3_ESM.pdf` - Transparent Peer Review
- `41467_2026_70417_MOESM4_ESM.xlsx` - Source Data

Run `scripts/fetch_official_assets.py --out vendor/nature` from a network-enabled clone.

Binary files should only be committed after their redistribution terms are checked. Their hashes should always be committed.
