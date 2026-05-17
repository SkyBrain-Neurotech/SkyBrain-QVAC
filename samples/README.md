# samples/

Drop EEG recordings here for ad-hoc testing. Binaries (`.edf`, `.edf+`,
`.bdf`, `.csv`, `.mat`) are gitignored so no patient data lands in the
public repo.

To generate a fresh synthetic recording:

```bash
skybrain-generate-edf --output samples/demo --duration 30 --channels 4 \
                       --pre-duration 10 --post-duration 10
```

That produces `samples/demo.edf` (a 30-second 4-channel synthetic EEG)
plus a `samples/demo_segments.csv` companion. Both are gitignored.

See [`docs/USER_GUIDE.md`](../docs/USER_GUIDE.md) for the full walkthrough.
