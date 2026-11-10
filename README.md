# ActivitySource process-context propagation performance artifact

- [Results and accepted checkpoint inventory](process-context-perf/RESULTS.md)
- [Full-precision combined results](process-context-perf/RESULTS.json)
- [Methodology, controls, uncertainty, and reproduction](process-context-perf/PERFORMANCE-METHODOLOGY.md)
- [Environment and binary manifest](process-context-perf/manifest.json)
- [Host constraints](process-context-perf/host-constraints.json)
- [Host monitor summary](process-context-perf/host-monitor-summary.json)
- [Accepted package inventory](PACKAGE-MANIFEST.json)

The three source project directories retain their original sibling layout. Run reproduction commands from `process-context-perf/`. The production instrumentation checkout must be obtained and built separately at the recorded commit.

Accepted raw Full JSON reports, console output, per-process native logs, source snapshots, and captured benchmark DLL/PDB proofs are included. The initial no-listener cohort has the disclosed legacy source-binding limitation; pooling it does not strengthen that provenance. Host monitoring covers complete checkpoint windows and does not establish exclusive CPU use. Discarded pilots are retained locally and excluded from this publication.

Verify staged file bytes from this directory with `sha256sum -c SHA256SUMS`. The checksum file covers every other packaged file.
