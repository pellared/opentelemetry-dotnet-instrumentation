# ActivitySource process-context factory measurements

**Complete**; generated 2026-11-10 02:26:12 UTC.

Analyzed 41/41 checkpoints, 640/640 processes, and 72/72 comparison rows. Missing results are omitted from numeric tables.

[Machine-readable combined statistics and per-block inputs](RESULTS.json).

Times are ns/op. The main tables use BenchmarkDotNet Result measurements after its measured empty-loop overhead subtraction. Each number is an equal-weight mean of independently launched process means. Δ is candidate minus baseline; brackets give a pointwise paired two-sided Student t95 interval on block differences. The primary baseline has the same profiler attached with PROCESS disabled and cached equivalent manual parent/link input.

Primary profiles use a minimal application ActivityListener with no application TracerProvider or exporters. Attached profiles still initialize SDK globals. A target-metadata SDK value of none means no application provider; it does not mean SDK assemblies are absent.

Each cohort has four balanced blocks (n=4, df=3). The .NET 10 Root, NoListeners, Dropped, AmbientParent, and SuppliedContext primary rows combine their original and one additional cohort as distinct cohort/block IDs; after both finish each uses all eight block differences (n=8, df=7). A partial n column such as 4/8 shows missing repeat coverage. All 20 Actual iterations per process are retained.

One additional four-block cohort for those five workloads was selected after observing between-process variation, rather than by the direction or significance of a result. That sample plan was then frozen. Intervals are nominal exploratory intervals; they are not adjusted for the earlier inspection or sequential selection.

Instrumentation commit: `536388a48532750a501e2bf94b36e7b946d69a82`. [Environment and binary/harness manifest](manifest.json).

## .NET 10 primary workloads

| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ B/op |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 8 | 376.86 → 477.82 | 100.96 [86.19, 115.73] | 0.00 |
| Root | link | 8 | 534.03 → 615.92 | 81.89 [66.09, 97.70] | 0.00 |
| RootEmptyLinks | parent | 4 | 380.68 → 477.54 | 96.86 [83.97, 109.74] | 0.00 |
| RootEmptyLinks | link | 4 | 519.04 → 738.61 | 219.57 [196.29, 242.84] | 128.00 |
| RootExistingLink | parent | 4 | 462.07 → 562.85 | 100.78 [87.75, 113.80] | 0.00 |
| RootExistingLink | link | 4 | 580.99 → 845.28 | 264.29 [241.29, 287.28] | 160.00 |
| RootAlreadyLinked | parent | 4 | 460.73 → 561.21 | 100.48 [80.38, 120.58] | 0.00 |
| RootAlreadyLinked | link | 4 | 540.58 → 774.44 | 233.86 [190.23, 277.49] | 160.00 |
| NoListeners | parent | 8 | 13.73 → 100.53 | 86.80 [75.73, 97.86] | 0.00 |
| NoListeners | link | 8 | 13.30 → 90.57 | 77.26 [75.36, 79.17] | 0.00 |
| Dropped | parent | 8 | 40.70 → 120.18 | 79.48 [75.67, 83.28] | 0.00 |
| Dropped | link | 8 | 54.38 → 122.68 | 68.31 [60.82, 75.79] | 0.00 |
| DropReadingLinks | parent | 4 | 63.82 → 142.41 | 78.59 [75.21, 81.96] | 0.00 |
| DropReadingLinks | link | 4 | 76.98 → 314.99 | 238.01 [221.17, 254.86] | 160.00 |
| AmbientParent | parent | 8 | 409.34 → 482.22 | 72.88 [65.38, 80.38] | 0.00 |
| AmbientParent | link | 8 | 404.41 → 481.98 | 77.57 [72.61, 82.53] | 0.00 |
| SuppliedContext | parent | 8 | 371.22 → 462.26 | 91.04 [74.21, 107.87] | 0.00 |
| SuppliedContext | link | 8 | 360.55 → 462.51 | 101.97 [95.95, 107.99] | 0.00 |
| SuppliedParentId | parent | 4 | 550.42 → 595.50 | 45.07 [30.89, 59.26] | 0.00 |
| SuppliedParentId | link | 4 | 543.59 → 611.55 | 67.96 [40.68, 95.23] | 0.00 |
| SuppliedEmptyParentId | parent | 4 | 478.52 → 515.12 | 36.60 [11.44, 61.76] | 0.00 |
| SuppliedEmptyParentId | link | 4 | 481.36 → 514.54 | 33.19 [8.14, 58.23] | 0.00 |
| CreateOnly | parent | 4 | 89.61 → 178.21 | 88.60 [85.53, 91.67] | 0.00 |
| CreateOnly | link | 4 | 198.72 → 270.80 | 72.08 [62.86, 81.31] | 0.00 |
| CreateThenStart | parent | 4 | 374.56 → 487.13 | 112.58 [73.77, 151.39] | 0.00 |
| CreateThenStart | link | 4 | 526.63 → 613.57 | 86.93 [79.61, 94.26] | 0.00 |
| PropagationOnly | parent | 4 | 374.62 → 479.59 | 104.97 [94.22, 115.73] | 0.00 |
| PropagationOnly | link | 4 | 529.79 → 616.13 | 86.34 [45.76, 126.92] | 0.00 |

<details>
<summary>Process ranges and raw Actual comparisons</summary>

Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction is a material fraction of the factory time.

| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 361.71–396.38 → 465.69–486.70 | 101.72 [86.99, 116.45] | 2.85–4.47 → 2.82–4.89 | 416.00 → 416.00 |
| Root | link | 511.82–584.57 → 603.41–638.23 | 81.21 [65.23, 97.18] | 2.81–4.45 → 2.81–4.78 | 632.00 → 632.00 |
| RootEmptyLinks | parent | 374.07–389.55 → 468.82–487.60 | 96.77 [82.69, 110.86] | 2.81–4.92 → 2.96–4.54 | 416.00 → 416.00 |
| RootEmptyLinks | link | 512.37–523.49 → 720.65–752.42 | 219.28 [196.12, 242.45] | 2.80–4.76 → 2.83–4.19 | 632.00 → 760.00 |
| RootExistingLink | parent | 451.72–467.67 → 556.24–570.81 | 100.69 [87.42, 113.96] | 2.87–4.47 → 2.84–4.26 | 544.00 → 544.00 |
| RootExistingLink | link | 573.74–590.01 → 838.00–856.77 | 264.07 [240.74, 287.40] | 4.15–4.40 → 2.84–4.48 | 696.00 → 856.00 |
| RootAlreadyLinked | parent | 456.81–466.89 → 547.37–574.83 | 100.22 [79.73, 120.72] | 4.20–4.42 → 3.82–4.43 | 544.00 → 544.00 |
| RootAlreadyLinked | link | 521.82–584.80 → 754.07–787.63 | 233.54 [190.88, 276.19] | 4.15–4.40 → 2.82–4.54 | 632.00 → 792.00 |
| NoListeners | parent | 12.60–13.95 → 93.70–133.36 | 86.71 [75.61, 97.82] | 2.80–4.11 → 2.80–2.94 | 0.00 → 0.00 |
| NoListeners | link | 12.09–13.91 → 88.43–94.02 | 76.86 [75.32, 78.41] | 2.79–4.60 → 2.80–4.12 | 0.00 → 0.00 |
| Dropped | parent | 38.02–42.68 → 116.66–127.95 | 78.29 [75.72, 80.87] | 2.83–7.17 → 2.80–4.44 | 0.00 → 0.00 |
| Dropped | link | 49.99–74.28 → 121.22–126.63 | 68.17 [61.25, 75.09] | 2.82–4.51 → 2.80–4.11 | 0.00 → 0.00 |
| DropReadingLinks | parent | 62.30–66.31 → 141.81–143.13 | 77.73 [75.11, 80.34] | 2.82–4.64 → 2.80–2.80 | 32.00 → 32.00 |
| DropReadingLinks | link | 75.59–79.74 → 307.19–328.53 | 238.42 [222.40, 254.44] | 2.81–4.13 → 2.95–4.68 | 32.00 → 192.00 |
| AmbientParent | parent | 402.92–430.31 → 478.44–484.59 | 73.41 [65.96, 80.87] | 2.86–4.93 → 2.95–4.96 | 432.00 → 432.00 |
| AmbientParent | link | 398.50–412.71 → 477.21–489.49 | 77.45 [72.72, 82.19] | 3.01–4.48 → 2.81–4.89 | 432.00 → 432.00 |
| SuppliedContext | parent | 357.70–425.66 → 452.15–474.39 | 91.02 [74.12, 107.92] | 2.80–4.92 → 2.93–4.66 | 416.00 → 416.00 |
| SuppliedContext | link | 355.01–366.27 → 449.76–469.53 | 101.77 [95.97, 107.57] | 2.80–4.49 → 2.96–4.91 | 416.00 → 416.00 |
| SuppliedParentId | parent | 545.82–558.69 → 584.78–602.32 | 45.58 [33.66, 57.49] | 2.90–4.28 → 2.84–4.90 | 560.00 → 560.00 |
| SuppliedParentId | link | 533.83–549.12 → 594.72–631.81 | 68.38 [40.13, 96.63] | 2.75–4.22 → 2.95–4.53 | 560.00 → 560.00 |
| SuppliedEmptyParentId | parent | 466.91–493.30 → 510.04–520.90 | 37.09 [10.60, 63.59] | 2.90–4.15 → 2.80–4.52 | 504.00 → 504.00 |
| SuppliedEmptyParentId | link | 459.71–508.20 → 507.95–520.34 | 32.82 [7.71, 57.92] | 2.75–4.91 → 2.82–4.15 | 504.00 → 504.00 |
| CreateOnly | parent | 89.20–89.80 → 176.22–180.57 | 89.00 [86.03, 91.98] | 4.71–6.27 → 5.08–7.17 | 200.00 → 200.00 |
| CreateOnly | link | 196.75–200.92 → 265.66–279.15 | 70.50 [61.02, 79.99] | 5.14–7.07 → 4.67–5.49 | 328.00 → 328.00 |
| CreateThenStart | parent | 371.19–379.36 → 472.54–520.12 | 112.94 [74.70, 151.17] | 2.85–4.19 → 2.81–4.17 | 416.00 → 416.00 |
| CreateThenStart | link | 525.16–528.32 → 611.31–618.53 | 86.66 [79.59, 93.74] | 2.87–4.42 → 2.81–4.45 | 632.00 → 632.00 |
| PropagationOnly | parent | 364.18–381.43 → 468.51–490.59 | 104.16 [91.97, 116.34] | 3.03–4.55 → 2.82–4.53 | 416.00 → 416.00 |
| PropagationOnly | link | 507.78–551.76 → 600.52–635.10 | 86.37 [47.47, 125.27] | 2.87–4.47 → 2.81–4.56 | 632.00 → 632.00 |

</details>

<details>
<summary>All paired process means, with distinct cohort/block IDs</summary>

Values are rounded here; the linked source analysis preserves full precision and all iterations. A control-baseline process can appear in more than one comparison.

| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Baseline Actual | Candidate Actual | Baseline B/op | Candidate B/op |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root | parent | activity-net10-root/B00 | 361.71 | 474.23 | 364.72 | 477.99 | 416.00 | 416.00 |
| Root | parent | activity-net10-root/B01 | 364.06 | 485.38 | 368.28 | 489.69 | 416.00 | 416.00 |
| Root | parent | activity-net10-root/B02 | 372.24 | 479.30 | 375.08 | 482.12 | 416.00 | 416.00 |
| Root | parent | activity-net10-root/B03 | 396.38 | 469.80 | 399.39 | 474.27 | 416.00 | 416.00 |
| Root | parent | activity-repeat-net10-root/B00 | 369.20 | 476.02 | 372.20 | 480.49 | 416.00 | 416.00 |
| Root | parent | activity-repeat-net10-root/B01 | 376.12 | 486.70 | 378.96 | 491.13 | 416.00 | 416.00 |
| Root | parent | activity-repeat-net10-root/B02 | 383.75 | 485.44 | 387.94 | 490.33 | 416.00 | 416.00 |
| Root | parent | activity-repeat-net10-root/B03 | 391.43 | 465.69 | 395.91 | 470.23 | 416.00 | 416.00 |
| Root | link | activity-net10-root/B00 | 528.23 | 606.40 | 531.04 | 609.21 | 632.00 | 632.00 |
| Root | link | activity-net10-root/B01 | 584.57 | 624.24 | 588.92 | 627.05 | 632.00 | 632.00 |
| Root | link | activity-net10-root/B02 | 519.82 | 610.27 | 522.64 | 613.08 | 632.00 | 632.00 |
| Root | link | activity-net10-root/B03 | 529.54 | 622.78 | 533.99 | 625.76 | 632.00 | 632.00 |
| Root | link | activity-repeat-net10-root/B00 | 529.30 | 608.15 | 533.71 | 610.98 | 632.00 | 632.00 |
| Root | link | activity-repeat-net10-root/B01 | 536.35 | 638.23 | 540.62 | 641.19 | 632.00 | 632.00 |
| Root | link | activity-repeat-net10-root/B02 | 532.58 | 613.87 | 536.76 | 618.65 | 632.00 | 632.00 |
| Root | link | activity-repeat-net10-root/B03 | 511.82 | 603.41 | 514.82 | 606.24 | 632.00 | 632.00 |
| RootEmptyLinks | parent | activity-net10-rootemptylinks/B00 | 377.32 | 484.40 | 380.13 | 488.57 | 416.00 | 416.00 |
| RootEmptyLinks | parent | activity-net10-rootemptylinks/B01 | 389.55 | 487.60 | 394.04 | 492.14 | 416.00 | 416.00 |
| RootEmptyLinks | parent | activity-net10-rootemptylinks/B02 | 374.07 | 468.82 | 378.99 | 471.78 | 416.00 | 416.00 |
| RootEmptyLinks | parent | activity-net10-rootemptylinks/B03 | 381.78 | 469.34 | 386.08 | 473.84 | 416.00 | 416.00 |
| RootEmptyLinks | link | activity-net10-rootemptylinks/B00 | 517.67 | 720.65 | 520.47 | 723.49 | 632.00 | 760.00 |
| RootEmptyLinks | link | activity-net10-rootemptylinks/B01 | 512.37 | 746.80 | 516.87 | 750.96 | 632.00 | 760.00 |
| RootEmptyLinks | link | activity-net10-rootemptylinks/B02 | 523.49 | 752.42 | 527.91 | 756.61 | 632.00 | 760.00 |
| RootEmptyLinks | link | activity-net10-rootemptylinks/B03 | 522.64 | 734.58 | 527.39 | 738.73 | 632.00 | 760.00 |
| RootExistingLink | parent | activity-net10-rootexistinglink/B00 | 451.72 | 557.77 | 454.71 | 562.03 | 544.00 | 544.00 |
| RootExistingLink | parent | activity-net10-rootexistinglink/B01 | 466.46 | 570.81 | 470.92 | 573.76 | 544.00 | 544.00 |
| RootExistingLink | parent | activity-net10-rootexistinglink/B02 | 467.67 | 556.24 | 471.89 | 560.40 | 544.00 | 544.00 |
| RootExistingLink | parent | activity-net10-rootexistinglink/B03 | 462.45 | 566.58 | 465.31 | 569.42 | 544.00 | 544.00 |
| RootExistingLink | link | activity-net10-rootexistinglink/B00 | 590.01 | 838.00 | 594.25 | 842.39 | 696.00 | 856.00 |
| RootExistingLink | link | activity-net10-rootexistinglink/B01 | 579.29 | 840.51 | 583.53 | 843.35 | 696.00 | 856.00 |
| RootExistingLink | link | activity-net10-rootexistinglink/B02 | 580.93 | 845.82 | 585.33 | 850.28 | 696.00 | 856.00 |
| RootExistingLink | link | activity-net10-rootexistinglink/B03 | 573.74 | 856.77 | 577.89 | 861.25 | 696.00 | 856.00 |
| RootAlreadyLinked | parent | activity-net10-rootalreadylinked/B00 | 456.81 | 574.83 | 461.01 | 579.27 | 544.00 | 544.00 |
| RootAlreadyLinked | parent | activity-net10-rootalreadylinked/B01 | 461.83 | 563.03 | 466.24 | 566.85 | 544.00 | 544.00 |
| RootAlreadyLinked | parent | activity-net10-rootalreadylinked/B02 | 457.40 | 547.37 | 461.70 | 551.51 | 544.00 | 544.00 |
| RootAlreadyLinked | parent | activity-net10-rootalreadylinked/B03 | 466.89 | 559.62 | 471.21 | 563.44 | 544.00 | 544.00 |
| RootAlreadyLinked | link | activity-net10-rootalreadylinked/B00 | 584.80 | 780.60 | 588.98 | 785.14 | 632.00 | 792.00 |
| RootAlreadyLinked | link | activity-net10-rootalreadylinked/B01 | 524.79 | 775.47 | 529.04 | 778.29 | 632.00 | 792.00 |
| RootAlreadyLinked | link | activity-net10-rootalreadylinked/B02 | 530.92 | 787.63 | 535.32 | 791.45 | 632.00 | 792.00 |
| RootAlreadyLinked | link | activity-net10-rootalreadylinked/B03 | 521.82 | 754.07 | 525.97 | 758.58 | 632.00 | 792.00 |
| NoListeners | parent | no-listener-net10/B00 | 13.95 | 133.36 | 16.75 | 136.17 | 0.00 | 0.00 |
| NoListeners | parent | no-listener-net10/B01 | 13.90 | 94.89 | 16.70 | 97.69 | 0.00 | 0.00 |
| NoListeners | parent | no-listener-net10/B02 | 13.93 | 97.28 | 16.73 | 100.20 | 0.00 | 0.00 |
| NoListeners | parent | no-listener-net10/B03 | 12.60 | 94.57 | 16.70 | 97.50 | 0.00 | 0.00 |
| NoListeners | parent | no-listener-repeat-net10/B00 | 13.90 | 93.70 | 16.70 | 96.63 | 0.00 | 0.00 |
| NoListeners | parent | no-listener-repeat-net10/B01 | 13.91 | 96.73 | 16.71 | 99.65 | 0.00 | 0.00 |
| NoListeners | parent | no-listener-repeat-net10/B02 | 13.91 | 96.99 | 16.71 | 99.93 | 0.00 | 0.00 |
| NoListeners | parent | no-listener-repeat-net10/B03 | 13.75 | 96.71 | 16.70 | 99.64 | 0.00 | 0.00 |
| NoListeners | link | no-listener-net10/B00 | 13.46 | 89.90 | 16.71 | 92.70 | 0.00 | 0.00 |
| NoListeners | link | no-listener-net10/B01 | 12.09 | 94.02 | 16.70 | 96.82 | 0.00 | 0.00 |
| NoListeners | link | no-listener-net10/B02 | 12.13 | 88.43 | 16.71 | 92.55 | 0.00 | 0.00 |
| NoListeners | link | no-listener-net10/B03 | 13.57 | 90.68 | 16.76 | 93.47 | 0.00 | 0.00 |
| NoListeners | link | no-listener-repeat-net10/B00 | 13.76 | 93.11 | 16.70 | 96.06 | 0.00 | 0.00 |
| NoListeners | link | no-listener-repeat-net10/B01 | 13.91 | 88.78 | 16.71 | 91.73 | 0.00 | 0.00 |
| NoListeners | link | no-listener-repeat-net10/B02 | 13.76 | 89.78 | 16.71 | 92.58 | 0.00 | 0.00 |
| NoListeners | link | no-listener-repeat-net10/B03 | 13.75 | 89.84 | 16.70 | 92.64 | 0.00 | 0.00 |
| Dropped | parent | activity-net10-dropped/B00 | 42.43 | 119.03 | 45.53 | 121.95 | 0.00 | 0.00 |
| Dropped | parent | activity-net10-dropped/B01 | 42.68 | 118.71 | 45.51 | 121.64 | 0.00 | 0.00 |
| Dropped | parent | activity-net10-dropped/B02 | 40.83 | 118.13 | 45.28 | 122.27 | 0.00 | 0.00 |
| Dropped | parent | activity-net10-dropped/B03 | 40.60 | 120.19 | 45.24 | 123.13 | 0.00 | 0.00 |
| Dropped | parent | activity-repeat-net10-dropped/B00 | 38.02 | 127.95 | 45.19 | 130.75 | 0.00 | 0.00 |
| Dropped | parent | activity-repeat-net10-dropped/B01 | 40.76 | 121.39 | 45.27 | 124.32 | 0.00 | 0.00 |
| Dropped | parent | activity-repeat-net10-dropped/B02 | 40.09 | 119.37 | 44.66 | 122.17 | 0.00 | 0.00 |
| Dropped | parent | activity-repeat-net10-dropped/B03 | 40.20 | 116.66 | 44.29 | 121.10 | 0.00 | 0.00 |
| Dropped | link | activity-net10-dropped/B00 | 51.61 | 121.23 | 54.58 | 124.18 | 0.00 | 0.00 |
| Dropped | link | activity-net10-dropped/B01 | 51.72 | 123.12 | 54.77 | 126.07 | 0.00 | 0.00 |
| Dropped | link | activity-net10-dropped/B02 | 49.99 | 126.63 | 54.50 | 129.44 | 0.00 | 0.00 |
| Dropped | link | activity-net10-dropped/B03 | 51.84 | 121.36 | 54.67 | 124.16 | 0.00 | 0.00 |
| Dropped | link | activity-repeat-net10-dropped/B00 | 74.28 | 121.22 | 77.11 | 125.33 | 0.00 | 0.00 |
| Dropped | link | activity-repeat-net10-dropped/B01 | 51.32 | 123.83 | 54.28 | 126.63 | 0.00 | 0.00 |
| Dropped | link | activity-repeat-net10-dropped/B02 | 51.50 | 121.35 | 54.47 | 124.15 | 0.00 | 0.00 |
| Dropped | link | activity-repeat-net10-dropped/B03 | 52.76 | 122.72 | 55.72 | 125.52 | 0.00 | 0.00 |
| DropReadingLinks | parent | activity-net10-dropreadinglinks/B00 | 62.30 | 143.13 | 66.94 | 145.93 | 32.00 | 32.00 |
| DropReadingLinks | parent | activity-net10-dropreadinglinks/B01 | 63.62 | 142.65 | 66.44 | 145.45 | 32.00 | 32.00 |
| DropReadingLinks | parent | activity-net10-dropreadinglinks/B02 | 63.06 | 141.81 | 67.29 | 144.61 | 32.00 | 32.00 |
| DropReadingLinks | parent | activity-net10-dropreadinglinks/B03 | 66.31 | 142.03 | 69.27 | 144.84 | 32.00 | 32.00 |
| DropReadingLinks | link | activity-net10-dropreadinglinks/B00 | 76.33 | 328.53 | 79.14 | 331.49 | 32.00 | 192.00 |
| DropReadingLinks | link | activity-net10-dropreadinglinks/B01 | 79.74 | 307.19 | 82.67 | 311.87 | 32.00 | 192.00 |
| DropReadingLinks | link | activity-net10-dropreadinglinks/B02 | 76.27 | 309.59 | 79.11 | 312.54 | 32.00 | 192.00 |
| DropReadingLinks | link | activity-net10-dropreadinglinks/B03 | 75.59 | 314.67 | 79.72 | 318.41 | 32.00 | 192.00 |
| AmbientParent | parent | activity-net10-ambientparent/B00 | 430.31 | 483.90 | 434.86 | 488.84 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net10-ambientparent/B01 | 407.48 | 481.57 | 411.75 | 485.37 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net10-ambientparent/B02 | 405.92 | 478.44 | 410.05 | 483.41 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net10-ambientparent/B03 | 407.61 | 484.57 | 410.62 | 487.52 | 432.00 | 432.00 |
| AmbientParent | parent | activity-repeat-net10-ambientparent/B00 | 402.92 | 484.59 | 407.85 | 489.49 | 432.00 | 432.00 |
| AmbientParent | parent | activity-repeat-net10-ambientparent/B01 | 405.44 | 483.31 | 409.56 | 487.70 | 432.00 | 432.00 |
| AmbientParent | parent | activity-repeat-net10-ambientparent/B02 | 411.53 | 478.74 | 414.39 | 483.21 | 432.00 | 432.00 |
| AmbientParent | parent | activity-repeat-net10-ambientparent/B03 | 403.55 | 482.65 | 406.67 | 487.54 | 432.00 | 432.00 |
| AmbientParent | link | activity-net10-ambientparent/B00 | 409.61 | 489.49 | 413.95 | 492.30 | 432.00 | 432.00 |
| AmbientParent | link | activity-net10-ambientparent/B01 | 412.71 | 480.18 | 416.83 | 484.66 | 432.00 | 432.00 |
| AmbientParent | link | activity-net10-ambientparent/B02 | 398.50 | 483.17 | 402.98 | 487.58 | 432.00 | 432.00 |
| AmbientParent | link | activity-net10-ambientparent/B03 | 407.34 | 477.21 | 410.35 | 480.18 | 432.00 | 432.00 |
| AmbientParent | link | activity-repeat-net10-ambientparent/B00 | 405.03 | 483.80 | 408.04 | 487.94 | 432.00 | 432.00 |
| AmbientParent | link | activity-repeat-net10-ambientparent/B01 | 400.00 | 481.53 | 404.28 | 484.37 | 432.00 | 432.00 |
| AmbientParent | link | activity-repeat-net10-ambientparent/B02 | 401.06 | 482.13 | 405.24 | 485.09 | 432.00 | 432.00 |
| AmbientParent | link | activity-repeat-net10-ambientparent/B03 | 401.06 | 478.36 | 404.06 | 483.26 | 432.00 | 432.00 |
| SuppliedContext | parent | activity-net10-suppliedcontext/B00 | 366.70 | 474.39 | 370.96 | 477.33 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net10-suppliedcontext/B01 | 366.28 | 452.15 | 369.10 | 456.37 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net10-suppliedcontext/B02 | 357.91 | 455.34 | 362.06 | 458.29 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net10-suppliedcontext/B03 | 425.66 | 470.59 | 430.58 | 474.99 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-repeat-net10-suppliedcontext/B00 | 374.23 | 461.52 | 378.37 | 465.72 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-repeat-net10-suppliedcontext/B01 | 358.19 | 457.95 | 362.68 | 461.88 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-repeat-net10-suppliedcontext/B02 | 363.06 | 467.13 | 365.86 | 471.80 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-repeat-net10-suppliedcontext/B03 | 357.70 | 458.99 | 361.51 | 462.92 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net10-suppliedcontext/B00 | 366.27 | 469.09 | 370.10 | 473.82 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net10-suppliedcontext/B01 | 363.54 | 453.52 | 366.34 | 458.43 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net10-suppliedcontext/B02 | 359.19 | 469.53 | 363.34 | 473.72 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net10-suppliedcontext/B03 | 359.00 | 469.34 | 363.14 | 472.38 | 416.00 | 416.00 |
| SuppliedContext | link | activity-repeat-net10-suppliedcontext/B00 | 357.90 | 456.49 | 362.03 | 459.44 | 416.00 | 416.00 |
| SuppliedContext | link | activity-repeat-net10-suppliedcontext/B01 | 363.19 | 466.53 | 367.31 | 469.49 | 416.00 | 416.00 |
| SuppliedContext | link | activity-repeat-net10-suppliedcontext/B02 | 360.28 | 465.85 | 364.43 | 470.36 | 416.00 | 416.00 |
| SuppliedContext | link | activity-repeat-net10-suppliedcontext/B03 | 355.01 | 449.76 | 359.50 | 452.72 | 416.00 | 416.00 |
| SuppliedParentId | parent | activity-net10-suppliedparentid/B00 | 558.69 | 594.60 | 561.59 | 599.05 | 560.00 | 560.00 |
| SuppliedParentId | parent | activity-net10-suppliedparentid/B01 | 549.10 | 602.32 | 553.37 | 605.15 | 560.00 | 560.00 |
| SuppliedParentId | parent | activity-net10-suppliedparentid/B02 | 548.09 | 600.29 | 552.33 | 604.44 | 560.00 | 560.00 |
| SuppliedParentId | parent | activity-net10-suppliedparentid/B03 | 545.82 | 584.78 | 548.71 | 589.68 | 560.00 | 560.00 |
| SuppliedParentId | link | activity-net10-suppliedparentid/B00 | 544.09 | 594.72 | 548.24 | 597.68 | 560.00 | 560.00 |
| SuppliedParentId | link | activity-net10-suppliedparentid/B01 | 549.12 | 605.07 | 552.16 | 609.27 | 560.00 | 560.00 |
| SuppliedParentId | link | activity-net10-suppliedparentid/B02 | 533.83 | 614.58 | 536.58 | 618.75 | 560.00 | 560.00 |
| SuppliedParentId | link | activity-net10-suppliedparentid/B03 | 547.32 | 631.81 | 551.54 | 636.33 | 560.00 | 560.00 |
| SuppliedEmptyParentId | parent | activity-net10-suppliedemptyparentid/B00 | 466.91 | 517.66 | 471.02 | 522.16 | 504.00 | 504.00 |
| SuppliedEmptyParentId | parent | activity-net10-suppliedemptyparentid/B01 | 480.76 | 511.88 | 483.65 | 516.40 | 504.00 | 504.00 |
| SuppliedEmptyParentId | parent | activity-net10-suppliedemptyparentid/B02 | 493.30 | 510.04 | 497.46 | 512.84 | 504.00 | 504.00 |
| SuppliedEmptyParentId | parent | activity-net10-suppliedemptyparentid/B03 | 473.12 | 520.90 | 476.01 | 525.12 | 504.00 | 504.00 |
| SuppliedEmptyParentId | link | activity-net10-suppliedemptyparentid/B00 | 477.47 | 518.92 | 482.37 | 521.74 | 504.00 | 504.00 |
| SuppliedEmptyParentId | link | activity-net10-suppliedemptyparentid/B01 | 459.71 | 507.95 | 462.61 | 510.92 | 504.00 | 504.00 |
| SuppliedEmptyParentId | link | activity-net10-suppliedemptyparentid/B02 | 480.05 | 510.96 | 482.80 | 515.10 | 504.00 | 504.00 |
| SuppliedEmptyParentId | link | activity-net10-suppliedemptyparentid/B03 | 508.20 | 520.34 | 512.02 | 523.31 | 504.00 | 504.00 |
| CreateOnly | parent | activity-net10-createonly/B00 | 89.72 | 176.22 | 94.43 | 183.39 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net10-createonly/B01 | 89.71 | 180.57 | 94.83 | 185.67 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net10-createonly/B02 | 89.80 | 179.22 | 94.52 | 184.29 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net10-createonly/B03 | 89.20 | 176.83 | 95.46 | 181.91 | 200.00 | 200.00 |
| CreateOnly | link | activity-net10-createonly/B00 | 196.86 | 266.34 | 203.93 | 271.83 | 328.00 | 328.00 |
| CreateOnly | link | activity-net10-createonly/B01 | 200.35 | 265.66 | 207.02 | 270.34 | 328.00 | 328.00 |
| CreateOnly | link | activity-net10-createonly/B02 | 196.75 | 272.06 | 201.89 | 276.79 | 328.00 | 328.00 |
| CreateOnly | link | activity-net10-createonly/B03 | 200.92 | 279.15 | 207.93 | 283.82 | 328.00 | 328.00 |
| CreateThenStart | parent | activity-net10-createthenstart/B00 | 372.24 | 476.12 | 375.08 | 479.84 | 416.00 | 416.00 |
| CreateThenStart | parent | activity-net10-createthenstart/B01 | 379.36 | 479.76 | 383.55 | 483.52 | 416.00 | 416.00 |
| CreateThenStart | parent | activity-net10-createthenstart/B02 | 375.44 | 472.54 | 378.44 | 476.71 | 416.00 | 416.00 |
| CreateThenStart | parent | activity-net10-createthenstart/B03 | 371.19 | 520.12 | 374.18 | 522.93 | 416.00 | 416.00 |
| CreateThenStart | link | activity-net10-createthenstart/B00 | 527.31 | 611.31 | 531.51 | 615.76 | 632.00 | 632.00 |
| CreateThenStart | link | activity-net10-createthenstart/B01 | 525.16 | 618.53 | 529.58 | 622.66 | 632.00 | 632.00 |
| CreateThenStart | link | activity-net10-createthenstart/B02 | 528.32 | 611.57 | 531.19 | 614.37 | 632.00 | 632.00 |
| CreateThenStart | link | activity-net10-createthenstart/B03 | 525.75 | 612.87 | 529.72 | 615.85 | 632.00 | 632.00 |
| PropagationOnly | parent | activity-net10-propagationonly/B00 | 372.54 | 482.19 | 377.02 | 485.13 | 416.00 | 416.00 |
| PropagationOnly | parent | activity-net10-propagationonly/B01 | 380.32 | 490.59 | 383.36 | 495.11 | 416.00 | 416.00 |
| PropagationOnly | parent | activity-net10-propagationonly/B02 | 381.43 | 477.09 | 385.90 | 480.05 | 416.00 | 416.00 |
| PropagationOnly | parent | activity-net10-propagationonly/B03 | 364.18 | 468.51 | 368.73 | 471.33 | 416.00 | 416.00 |
| PropagationOnly | link | activity-net10-propagationonly/B00 | 540.38 | 635.10 | 544.83 | 637.92 | 632.00 | 632.00 |
| PropagationOnly | link | activity-net10-propagationonly/B01 | 551.76 | 600.52 | 554.76 | 605.08 | 632.00 | 632.00 |
| PropagationOnly | link | activity-net10-propagationonly/B02 | 507.78 | 613.30 | 512.24 | 616.28 | 632.00 | 632.00 |
| PropagationOnly | link | activity-net10-propagationonly/B03 | 519.22 | 615.58 | 522.09 | 620.14 | 632.00 | 632.00 |

</details>

## .NET 8 subset

| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ B/op |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 4 | 487.40 → 585.26 | 97.87 [71.99, 123.74] | 0.00 |
| Root | link | 4 | 692.79 → 765.50 | 72.71 [43.35, 102.08] | 0.00 |
| NoListeners | parent | 4 | 36.80 → 113.06 | 76.25 [75.31, 77.19] | 0.00 |
| NoListeners | link | 4 | 36.78 → 106.19 | 69.40 [66.32, 72.48] | 0.00 |
| Dropped | parent | 4 | 89.52 → 167.40 | 77.88 [74.79, 80.98] | 0.00 |
| Dropped | link | 4 | 95.68 → 158.99 | 63.31 [57.40, 69.22] | 0.00 |
| AmbientParent | parent | 4 | 527.49 → 596.60 | 69.11 [55.16, 83.05] | 0.00 |
| AmbientParent | link | 4 | 526.28 → 598.01 | 71.73 [42.93, 100.53] | 0.00 |
| SuppliedContext | parent | 4 | 497.06 → 564.14 | 67.08 [42.68, 91.48] | 0.00 |
| SuppliedContext | link | 4 | 499.74 → 557.77 | 58.02 [39.81, 76.24] | 0.00 |
| CreateOnly | parent | 4 | 163.31 → 240.68 | 77.37 [73.62, 81.12] | 0.00 |
| CreateOnly | link | 4 | 251.66 → 323.56 | 71.90 [44.99, 98.81] | 0.00 |

<details>
<summary>Process ranges and raw Actual comparisons</summary>

Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction is a material fraction of the factory time.

| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 483.35–496.17 → 574.59–601.54 | 97.35 [71.03, 123.67] | 4.14–4.57 → 2.80–4.20 | 416.00 → 416.00 |
| Root | link | 675.95–699.81 → 747.78–781.64 | 72.03 [42.34, 101.72] | 2.82–4.21 → 2.82–4.16 | 632.00 → 632.00 |
| NoListeners | parent | 36.77–36.84 → 112.35–113.69 | 76.58 [76.00, 77.17] | 2.79–2.80 → 2.80–4.11 | 0.00 → 0.00 |
| NoListeners | link | 36.71–36.84 → 103.37–107.58 | 69.71 [67.56, 71.86] | 2.80–2.80 → 2.80–4.00 | 0.00 → 0.00 |
| Dropped | parent | 89.21–89.86 → 164.76–169.23 | 77.89 [74.78, 80.99] | 2.80–2.81 → 2.81–2.81 | 0.00 → 0.00 |
| Dropped | link | 94.82–96.29 → 156.30–164.64 | 63.32 [57.41, 69.22] | 2.80–2.80 → 2.80–2.81 | 0.00 → 0.00 |
| AmbientParent | parent | 525.41–529.96 → 584.97–602.67 | 69.48 [55.68, 83.28] | 2.80–4.19 → 2.81–4.49 | 432.00 → 432.00 |
| AmbientParent | link | 525.19–528.03 → 585.66–624.59 | 71.58 [42.99, 100.16] | 4.13–4.51 → 4.16–4.18 | 432.00 → 432.00 |
| SuppliedContext | parent | 492.97–500.34 → 545.41–572.42 | 67.19 [42.92, 91.45] | 2.82–4.01 → 2.80–4.19 | 416.00 → 416.00 |
| SuppliedContext | link | 497.10–502.57 → 544.53–567.17 | 57.02 [38.22, 75.82] | 3.97–4.17 → 2.80–3.94 | 416.00 → 416.00 |
| CreateOnly | parent | 161.49–164.72 → 238.21–245.56 | 77.79 [74.81, 80.77] | 5.07–5.48 → 5.08–7.13 | 200.00 → 200.00 |
| CreateOnly | link | 248.45–255.25 → 312.56–344.72 | 71.43 [44.56, 98.30] | 5.08–6.64 → 5.10–5.52 | 328.00 → 328.00 |

</details>

<details>
<summary>All paired process means, with distinct cohort/block IDs</summary>

Values are rounded here; the linked source analysis preserves full precision and all iterations. A control-baseline process can appear in more than one comparison.

| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Baseline Actual | Candidate Actual | Baseline B/op | Candidate B/op |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root | parent | activity-net8-root/B00 | 483.96 | 601.54 | 488.18 | 605.74 | 416.00 | 416.00 |
| Root | parent | activity-net8-root/B01 | 483.35 | 577.46 | 487.93 | 580.27 | 416.00 | 416.00 |
| Root | parent | activity-net8-root/B02 | 486.10 | 587.46 | 490.25 | 591.65 | 416.00 | 416.00 |
| Root | parent | activity-net8-root/B03 | 496.17 | 574.59 | 500.67 | 578.76 | 416.00 | 416.00 |
| Root | link | activity-net8-root/B00 | 699.81 | 767.74 | 702.62 | 770.56 | 632.00 | 632.00 |
| Root | link | activity-net8-root/B01 | 699.10 | 747.78 | 703.28 | 750.60 | 632.00 | 632.00 |
| Root | link | activity-net8-root/B02 | 675.95 | 764.83 | 680.17 | 767.65 | 632.00 | 632.00 |
| Root | link | activity-net8-root/B03 | 696.29 | 781.64 | 700.43 | 785.80 | 632.00 | 632.00 |
| NoListeners | parent | activity-net8-nolisteners/B00 | 36.78 | 113.69 | 39.58 | 116.50 | 0.00 | 0.00 |
| NoListeners | parent | activity-net8-nolisteners/B01 | 36.84 | 112.35 | 39.64 | 116.46 | 0.00 | 0.00 |
| NoListeners | parent | activity-net8-nolisteners/B02 | 36.77 | 112.88 | 39.57 | 115.68 | 0.00 | 0.00 |
| NoListeners | parent | activity-net8-nolisteners/B03 | 36.83 | 113.30 | 39.62 | 116.11 | 0.00 | 0.00 |
| NoListeners | link | activity-net8-nolisteners/B00 | 36.84 | 107.58 | 39.64 | 110.38 | 0.00 | 0.00 |
| NoListeners | link | activity-net8-nolisteners/B01 | 36.71 | 107.18 | 39.50 | 109.99 | 0.00 | 0.00 |
| NoListeners | link | activity-net8-nolisteners/B02 | 36.82 | 103.37 | 39.62 | 107.38 | 0.00 | 0.00 |
| NoListeners | link | activity-net8-nolisteners/B03 | 36.76 | 106.61 | 39.55 | 109.41 | 0.00 | 0.00 |
| Dropped | parent | activity-net8-dropped/B00 | 89.86 | 169.23 | 92.66 | 172.04 | 0.00 | 0.00 |
| Dropped | parent | activity-net8-dropped/B01 | 89.61 | 164.76 | 92.42 | 167.57 | 0.00 | 0.00 |
| Dropped | parent | activity-net8-dropped/B02 | 89.39 | 168.56 | 92.19 | 171.37 | 0.00 | 0.00 |
| Dropped | parent | activity-net8-dropped/B03 | 89.21 | 167.05 | 92.01 | 169.86 | 0.00 | 0.00 |
| Dropped | link | activity-net8-dropped/B00 | 96.29 | 157.32 | 99.09 | 160.12 | 0.00 | 0.00 |
| Dropped | link | activity-net8-dropped/B01 | 94.82 | 156.30 | 97.62 | 159.11 | 0.00 | 0.00 |
| Dropped | link | activity-net8-dropped/B02 | 95.79 | 164.64 | 98.59 | 167.45 | 0.00 | 0.00 |
| Dropped | link | activity-net8-dropped/B03 | 95.83 | 157.71 | 98.63 | 160.52 | 0.00 | 0.00 |
| AmbientParent | parent | activity-net8-ambientparent/B00 | 525.41 | 596.30 | 529.60 | 599.13 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net8-ambientparent/B01 | 526.09 | 602.67 | 528.92 | 607.16 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net8-ambientparent/B02 | 529.96 | 602.45 | 532.78 | 605.27 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net8-ambientparent/B03 | 528.51 | 584.97 | 531.31 | 588.97 | 432.00 | 432.00 |
| AmbientParent | link | activity-net8-ambientparent/B00 | 528.03 | 592.70 | 532.20 | 596.88 | 432.00 | 432.00 |
| AmbientParent | link | activity-net8-ambientparent/B01 | 526.06 | 589.08 | 530.53 | 593.24 | 432.00 | 432.00 |
| AmbientParent | link | activity-net8-ambientparent/B02 | 525.84 | 624.59 | 530.35 | 628.75 | 432.00 | 432.00 |
| AmbientParent | link | activity-net8-ambientparent/B03 | 525.19 | 585.66 | 529.32 | 589.83 | 432.00 | 432.00 |
| SuppliedContext | parent | activity-net8-suppliedcontext/B00 | 492.97 | 572.42 | 495.81 | 575.22 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net8-suppliedcontext/B01 | 500.06 | 568.69 | 503.94 | 572.84 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net8-suppliedcontext/B02 | 494.86 | 570.04 | 497.68 | 572.86 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net8-suppliedcontext/B03 | 500.34 | 545.41 | 504.35 | 549.60 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net8-suppliedcontext/B00 | 499.26 | 567.17 | 503.23 | 571.12 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net8-suppliedcontext/B01 | 500.05 | 564.16 | 504.22 | 566.97 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net8-suppliedcontext/B02 | 502.57 | 544.53 | 506.70 | 547.36 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net8-suppliedcontext/B03 | 497.10 | 555.21 | 501.24 | 558.03 | 416.00 | 416.00 |
| CreateOnly | parent | activity-net8-createonly/B00 | 162.57 | 238.94 | 167.70 | 244.02 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net8-createonly/B01 | 164.43 | 240.00 | 169.51 | 247.14 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net8-createonly/B02 | 161.49 | 238.21 | 166.56 | 243.31 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net8-createonly/B03 | 164.72 | 245.56 | 170.20 | 250.68 | 200.00 | 200.00 |
| CreateOnly | link | activity-net8-createonly/B00 | 255.25 | 312.56 | 260.33 | 317.67 | 328.00 | 328.00 |
| CreateOnly | link | activity-net8-createonly/B01 | 251.79 | 317.38 | 258.43 | 322.89 | 328.00 | 328.00 |
| CreateOnly | link | activity-net8-createonly/B02 | 251.16 | 319.59 | 256.66 | 324.70 | 328.00 | 328.00 |
| CreateOnly | link | activity-net8-createonly/B03 | 248.45 | 344.72 | 253.96 | 349.82 | 328.00 | 328.00 |

</details>

## .NET 9 subset

| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ B/op |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 4 | 455.18 → 534.83 | 79.65 [48.98, 110.32] | 0.00 |
| Root | link | 4 | 647.95 → 711.61 | 63.66 [8.12, 119.20] | 0.00 |
| NoListeners | parent | 4 | 36.85 → 112.62 | 75.77 [58.49, 93.04] | 0.00 |
| NoListeners | link | 4 | 36.70 → 101.28 | 64.58 [63.11, 66.06] | 0.00 |
| Dropped | parent | 4 | 72.81 → 131.65 | 58.84 [58.13, 59.55] | 0.00 |
| Dropped | link | 4 | 80.50 → 134.51 | 54.01 [52.60, 55.41] | 0.00 |
| AmbientParent | parent | 4 | 471.07 → 544.54 | 73.47 [49.52, 97.42] | 0.00 |
| AmbientParent | link | 4 | 470.14 → 550.73 | 80.58 [69.73, 91.44] | 0.00 |
| SuppliedContext | parent | 4 | 458.73 → 511.41 | 52.68 [26.57, 78.79] | 0.00 |
| SuppliedContext | link | 4 | 459.55 → 510.77 | 51.22 [31.51, 70.93] | 0.00 |
| CreateOnly | parent | 4 | 142.30 → 199.77 | 57.47 [52.88, 62.07] | 0.00 |
| CreateOnly | link | 4 | 237.35 → 304.59 | 67.24 [51.41, 83.07] | 0.00 |

<details>
<summary>Process ranges and raw Actual comparisons</summary>

Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction is a material fraction of the factory time.

| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 448.32–460.60 → 521.40–552.88 | 79.76 [49.30, 110.22] | 2.96–4.34 → 3.73–4.48 | 416.00 → 416.00 |
| Root | link | 628.52–683.39 → 695.26–717.47 | 62.84 [7.45, 118.23] | 2.96–5.00 → 2.82–3.86 | 632.00 → 632.00 |
| NoListeners | parent | 36.76–36.90 → 106.66–128.92 | 76.03 [58.89, 93.17] | 2.79–2.95 → 2.80–3.69 | 0.00 → 0.00 |
| NoListeners | link | 36.60–36.76 → 100.13–102.10 | 64.70 [63.31, 66.09] | 2.79–2.95 → 2.95–2.96 | 0.00 → 0.00 |
| Dropped | parent | 71.78–73.55 → 130.56–132.56 | 57.96 [56.12, 59.80] | 2.95–4.58 → 2.80–2.81 | 0.00 → 0.00 |
| Dropped | link | 79.33–81.36 → 132.26–135.44 | 54.43 [53.67, 55.19] | 2.80–2.95 → 2.95–4.51 | 0.00 → 0.00 |
| AmbientParent | parent | 466.98–475.50 → 534.47–562.30 | 72.92 [49.59, 96.25] | 2.97–4.49 → 2.92–3.95 | 432.00 → 432.00 |
| AmbientParent | link | 465.31–472.63 → 541.12–557.36 | 80.17 [70.67, 89.66] | 2.96–4.18 → 2.83–3.83 | 432.00 → 432.00 |
| SuppliedContext | parent | 441.78–468.78 → 504.43–518.65 | 52.85 [28.30, 77.40] | 2.82–4.17 → 2.81–4.54 | 416.00 → 416.00 |
| SuppliedContext | link | 458.36–461.00 → 503.44–528.77 | 51.88 [32.93, 70.83] | 2.83–4.13 → 2.98–4.52 | 416.00 → 416.00 |
| CreateOnly | parent | 140.40–145.91 → 198.22–200.78 | 57.59 [52.80, 62.38] | 5.08–5.10 → 5.11–5.50 | 200.00 → 200.00 |
| CreateOnly | link | 232.46–241.26 → 295.57–310.24 | 67.00 [50.71, 83.28] | 5.10–7.47 → 5.11–6.71 | 328.00 → 328.00 |

</details>

<details>
<summary>All paired process means, with distinct cohort/block IDs</summary>

Values are rounded here; the linked source analysis preserves full precision and all iterations. A control-baseline process can appear in more than one comparison.

| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Baseline Actual | Candidate Actual | Baseline B/op | Candidate B/op |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root | parent | activity-net9-root/B00 | 460.60 | 527.38 | 463.57 | 531.21 | 416.00 | 416.00 |
| Root | parent | activity-net9-root/B01 | 452.74 | 537.68 | 456.91 | 541.41 | 416.00 | 416.00 |
| Root | parent | activity-net9-root/B02 | 459.07 | 521.40 | 463.35 | 525.56 | 416.00 | 416.00 |
| Root | parent | activity-net9-root/B03 | 448.32 | 552.88 | 452.65 | 557.35 | 416.00 | 416.00 |
| Root | link | activity-net9-root/B00 | 638.52 | 717.15 | 642.74 | 719.98 | 632.00 | 632.00 |
| Root | link | activity-net9-root/B01 | 683.39 | 695.26 | 687.89 | 699.03 | 632.00 | 632.00 |
| Root | link | activity-net9-root/B02 | 641.37 | 717.47 | 644.33 | 720.43 | 632.00 | 632.00 |
| Root | link | activity-net9-root/B03 | 628.52 | 716.55 | 633.53 | 720.41 | 632.00 | 632.00 |
| NoListeners | parent | activity-net9-nolisteners/B00 | 36.90 | 106.89 | 39.69 | 109.83 | 0.00 | 0.00 |
| NoListeners | parent | activity-net9-nolisteners/B01 | 36.86 | 108.01 | 39.65 | 110.81 | 0.00 | 0.00 |
| NoListeners | parent | activity-net9-nolisteners/B02 | 36.76 | 106.66 | 39.71 | 110.35 | 0.00 | 0.00 |
| NoListeners | parent | activity-net9-nolisteners/B03 | 36.88 | 128.92 | 39.68 | 131.85 | 0.00 | 0.00 |
| NoListeners | link | activity-net9-nolisteners/B00 | 36.76 | 101.09 | 39.55 | 104.04 | 0.00 | 0.00 |
| NoListeners | link | activity-net9-nolisteners/B01 | 36.73 | 100.13 | 39.52 | 103.07 | 0.00 | 0.00 |
| NoListeners | link | activity-net9-nolisteners/B02 | 36.60 | 102.10 | 39.55 | 105.05 | 0.00 | 0.00 |
| NoListeners | link | activity-net9-nolisteners/B03 | 36.71 | 101.81 | 39.52 | 104.77 | 0.00 | 0.00 |
| Dropped | parent | activity-net9-dropped/B00 | 71.78 | 130.56 | 76.36 | 133.36 | 0.00 | 0.00 |
| Dropped | parent | activity-net9-dropped/B01 | 72.68 | 130.95 | 76.83 | 133.75 | 0.00 | 0.00 |
| Dropped | parent | activity-net9-dropped/B02 | 73.55 | 132.51 | 76.50 | 135.32 | 0.00 | 0.00 |
| Dropped | parent | activity-net9-dropped/B03 | 73.22 | 132.56 | 76.28 | 135.37 | 0.00 | 0.00 |
| Dropped | link | activity-net9-dropped/B00 | 79.33 | 132.26 | 82.28 | 136.76 | 0.00 | 0.00 |
| Dropped | link | activity-net9-dropped/B01 | 81.17 | 135.08 | 83.96 | 138.03 | 0.00 | 0.00 |
| Dropped | link | activity-net9-dropped/B02 | 80.16 | 135.24 | 83.10 | 138.20 | 0.00 | 0.00 |
| Dropped | link | activity-net9-dropped/B03 | 81.36 | 135.44 | 84.30 | 138.39 | 0.00 | 0.00 |
| AmbientParent | parent | activity-net9-ambientparent/B00 | 468.25 | 534.47 | 472.38 | 538.22 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net9-ambientparent/B01 | 473.54 | 544.37 | 476.51 | 548.31 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net9-ambientparent/B02 | 466.98 | 562.30 | 471.47 | 565.23 | 432.00 | 432.00 |
| AmbientParent | parent | activity-net9-ambientparent/B03 | 475.50 | 537.02 | 479.65 | 539.94 | 432.00 | 432.00 |
| AmbientParent | link | activity-net9-ambientparent/B00 | 470.66 | 541.12 | 473.62 | 544.95 | 432.00 | 432.00 |
| AmbientParent | link | activity-net9-ambientparent/B01 | 465.31 | 548.71 | 468.27 | 551.53 | 432.00 | 432.00 |
| AmbientParent | link | activity-net9-ambientparent/B02 | 472.63 | 555.72 | 476.79 | 558.70 | 432.00 | 432.00 |
| AmbientParent | link | activity-net9-ambientparent/B03 | 471.98 | 557.36 | 476.16 | 560.34 | 432.00 | 432.00 |
| SuppliedContext | parent | activity-net9-suppliedcontext/B00 | 460.25 | 507.00 | 463.06 | 511.48 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net9-suppliedcontext/B01 | 441.78 | 518.65 | 445.95 | 521.59 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net9-suppliedcontext/B02 | 468.78 | 515.54 | 472.94 | 518.36 | 416.00 | 416.00 |
| SuppliedContext | parent | activity-net9-suppliedcontext/B03 | 464.10 | 504.43 | 467.05 | 508.97 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net9-suppliedcontext/B00 | 459.82 | 506.04 | 463.96 | 509.79 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net9-suppliedcontext/B01 | 458.36 | 503.44 | 461.19 | 507.62 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net9-suppliedcontext/B02 | 461.00 | 504.84 | 463.83 | 509.36 | 416.00 | 416.00 |
| SuppliedContext | link | activity-net9-suppliedcontext/B03 | 459.03 | 528.77 | 462.01 | 531.74 | 416.00 | 416.00 |
| CreateOnly | parent | activity-net9-createonly/B00 | 140.40 | 200.37 | 145.49 | 205.87 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net9-createonly/B01 | 145.91 | 199.73 | 151.01 | 204.84 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net9-createonly/B02 | 141.72 | 198.22 | 146.81 | 203.35 | 200.00 | 200.00 |
| CreateOnly | parent | activity-net9-createonly/B03 | 141.18 | 200.78 | 146.28 | 205.90 | 200.00 | 200.00 |
| CreateOnly | link | activity-net9-createonly/B00 | 241.00 | 305.56 | 248.06 | 311.87 | 328.00 | 328.00 |
| CreateOnly | link | activity-net9-createonly/B01 | 232.46 | 306.98 | 237.56 | 313.69 | 328.00 | 328.00 |
| CreateOnly | link | activity-net9-createonly/B02 | 241.26 | 295.57 | 246.74 | 300.68 | 328.00 | 328.00 |
| CreateOnly | link | activity-net9-createonly/B03 | 234.67 | 310.24 | 242.14 | 316.23 | 328.00 | 328.00 |

</details>

## .NET 10 registration and profiler controls

These controls compare each candidate with the attached-profiler PROCESS-disabled baseline. NoAgent removes the profiler/startup hook; its difference includes whole-agent and JIT effects.

| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ B/op |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | Disabled → NoIncoming | 4 | 436.79 → 433.04 | -3.74 [-37.40, 29.91] | 0.00 |
| Root | Disabled → ExtractionOff | 4 | 436.79 → 426.79 | -10.00 [-44.03, 24.04] | 0.00 |
| Root | Disabled → NoAgent | 4 | 436.79 → 417.02 | -19.76 [-49.41, 9.88] | -88.00 |
| NoListeners | Disabled → NoIncoming | 4 | 13.42 → 13.80 | 0.38 [-0.83, 1.58] | 0.00 |
| NoListeners | Disabled → ExtractionOff | 4 | 13.42 → 13.83 | 0.41 [-0.91, 1.73] | 0.00 |
| NoListeners | Disabled → NoAgent | 4 | 13.42 → 14.81 | 1.39 [-0.11, 2.90] | 0.00 |

<details>
<summary>Process ranges and raw Actual comparisons</summary>

Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction is a material fraction of the factory time.

| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | Disabled → NoIncoming | 422.98–458.36 → 427.05–440.85 | -3.77 [-35.15, 27.60] | 2.86–4.40 → 2.86–4.49 | 504.00 → 504.00 |
| Root | Disabled → ExtractionOff | 422.98–458.36 → 419.98–434.92 | -10.03 [-42.32, 22.25] | 2.86–4.40 → 2.75–4.50 | 504.00 → 504.00 |
| Root | Disabled → NoAgent | 422.98–458.36 → 412.46–421.69 | -20.16 [-49.33, 9.00] | 2.86–4.40 → 2.81–4.28 | 504.00 → 416.00 |
| NoListeners | Disabled → NoIncoming | 12.26–13.91 → 13.74–13.90 | -0.00 [-0.09, 0.08] | 2.79–4.52 → 2.80–2.97 | 0.00 → 0.00 |
| NoListeners | Disabled → ExtractionOff | 12.26–13.91 → 13.75–13.90 | -0.02 [-0.08, 0.04] | 2.79–4.52 → 2.80–2.95 | 0.00 → 0.00 |
| NoListeners | Disabled → NoAgent | 12.26–13.91 → 14.34–15.00 | 1.36 [0.80, 1.92] | 2.79–4.52 → 2.94–4.25 | 0.00 → 0.00 |

</details>

<details>
<summary>All paired process means, with distinct cohort/block IDs</summary>

Values are rounded here; the linked source analysis preserves full precision and all iterations. A control-baseline process can appear in more than one comparison.

| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Baseline Actual | Candidate Actual | Baseline B/op | Candidate B/op |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root | Disabled → NoIncoming | controls-net10-root/B00 | 436.74 | 427.42 | 439.80 | 431.91 | 504.00 | 504.00 |
| Root | Disabled → NoIncoming | controls-net10-root/B01 | 458.36 | 427.05 | 461.22 | 431.23 | 504.00 | 504.00 |
| Root | Disabled → NoIncoming | controls-net10-root/B02 | 429.07 | 440.85 | 433.26 | 443.70 | 504.00 | 504.00 |
| Root | Disabled → NoIncoming | controls-net10-root/B03 | 422.98 | 436.85 | 427.38 | 439.71 | 504.00 | 504.00 |
| Root | Disabled → ExtractionOff | controls-net10-root/B00 | 436.74 | 422.12 | 439.80 | 424.98 | 504.00 | 504.00 |
| Root | Disabled → ExtractionOff | controls-net10-root/B01 | 458.36 | 419.98 | 461.22 | 424.48 | 504.00 | 504.00 |
| Root | Disabled → ExtractionOff | controls-net10-root/B02 | 429.07 | 434.92 | 433.26 | 437.66 | 504.00 | 504.00 |
| Root | Disabled → ExtractionOff | controls-net10-root/B03 | 422.98 | 430.14 | 427.38 | 434.39 | 504.00 | 504.00 |
| Root | Disabled → NoAgent | controls-net10-root/B00 | 436.74 | 416.42 | 439.80 | 419.23 | 504.00 | 416.00 |
| Root | Disabled → NoAgent | controls-net10-root/B01 | 458.36 | 412.46 | 461.22 | 415.28 | 504.00 | 416.00 |
| Root | Disabled → NoAgent | controls-net10-root/B02 | 429.07 | 421.69 | 433.26 | 425.97 | 504.00 | 416.00 |
| Root | Disabled → NoAgent | controls-net10-root/B03 | 422.98 | 417.51 | 427.38 | 420.53 | 504.00 | 416.00 |
| NoListeners | Disabled → NoIncoming | controls-net10-nolisteners/B00 | 13.75 | 13.80 | 16.70 | 16.75 | 0.00 | 0.00 |
| NoListeners | Disabled → NoIncoming | controls-net10-nolisteners/B01 | 13.76 | 13.90 | 16.70 | 16.70 | 0.00 | 0.00 |
| NoListeners | Disabled → NoIncoming | controls-net10-nolisteners/B02 | 13.91 | 13.74 | 16.71 | 16.71 | 0.00 | 0.00 |
| NoListeners | Disabled → NoIncoming | controls-net10-nolisteners/B03 | 12.26 | 13.75 | 16.78 | 16.70 | 0.00 | 0.00 |
| NoListeners | Disabled → ExtractionOff | controls-net10-nolisteners/B00 | 13.75 | 13.76 | 16.70 | 16.70 | 0.00 | 0.00 |
| NoListeners | Disabled → ExtractionOff | controls-net10-nolisteners/B01 | 13.76 | 13.90 | 16.70 | 16.70 | 0.00 | 0.00 |
| NoListeners | Disabled → ExtractionOff | controls-net10-nolisteners/B02 | 13.91 | 13.75 | 16.71 | 16.70 | 0.00 | 0.00 |
| NoListeners | Disabled → ExtractionOff | controls-net10-nolisteners/B03 | 12.26 | 13.90 | 16.78 | 16.70 | 0.00 | 0.00 |
| NoListeners | Disabled → NoAgent | controls-net10-nolisteners/B00 | 13.75 | 14.96 | 16.70 | 17.90 | 0.00 | 0.00 |
| NoListeners | Disabled → NoAgent | controls-net10-nolisteners/B01 | 13.76 | 15.00 | 16.70 | 17.94 | 0.00 | 0.00 |
| NoListeners | Disabled → NoAgent | controls-net10-nolisteners/B02 | 13.91 | 14.34 | 16.71 | 18.59 | 0.00 | 0.00 |
| NoListeners | Disabled → NoAgent | controls-net10-nolisteners/B03 | 12.26 | 14.95 | 16.78 | 17.90 | 0.00 | 0.00 |

</details>

## .NET 10 tiering disabled sensitivity

Sensitivity only: DOTNET_TieredCompilation=0 in every profile.

| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ B/op |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 4 | 576.95 → 697.90 | 120.95 [103.31, 138.59] | 0.00 |
| Root | link | 4 | 814.78 → 944.22 | 129.43 [114.12, 144.75] | 0.00 |
| NoListeners | parent | 4 | 38.05 → 134.60 | 96.55 [88.41, 104.69] | 0.00 |
| NoListeners | link | 4 | 37.92 → 131.67 | 93.76 [92.06, 95.45] | 0.00 |
| AmbientParent | parent | 4 | 667.95 → 796.27 | 128.32 [110.53, 146.11] | 0.00 |
| AmbientParent | link | 4 | 671.53 → 797.30 | 125.77 [108.74, 142.79] | 0.00 |

<details>
<summary>Process ranges and raw Actual comparisons</summary>

Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction is a material fraction of the factory time.

| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 567.58–582.93 → 692.23–705.16 | 120.93 [103.29, 138.56] | 2.53–2.55 → 2.51–2.54 | 416.00 → 416.00 |
| Root | link | 804.14–819.30 → 935.03–956.97 | 129.44 [114.13, 144.76] | 2.53–2.56 → 2.55–2.56 | 632.00 → 632.00 |
| NoListeners | parent | 37.76–38.87 → 131.44–141.91 | 96.57 [88.46, 104.67] | 2.49–2.52 → 2.50–2.53 | 0.00 → 0.00 |
| NoListeners | link | 37.76–38.27 → 130.61–133.12 | 93.77 [92.08, 95.46] | 2.49–2.52 → 2.50–2.53 | 0.00 → 0.00 |
| AmbientParent | parent | 662.14–679.05 → 792.31–802.52 | 128.33 [110.54, 146.12] | 2.52–2.54 → 2.53–2.55 | 432.00 → 432.00 |
| AmbientParent | link | 666.07–682.23 → 782.28–810.65 | 125.77 [108.73, 142.81] | 2.51–2.55 → 2.52–2.53 | 432.00 → 432.00 |

</details>

<details>
<summary>All paired process means, with distinct cohort/block IDs</summary>

Values are rounded here; the linked source analysis preserves full precision and all iterations. A control-baseline process can appear in more than one comparison.

| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Baseline Actual | Candidate Actual | Baseline B/op | Candidate B/op |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root | parent | tiering-off-net10-root/B00 | 567.58 | 705.16 | 570.12 | 707.67 | 416.00 | 416.00 |
| Root | parent | tiering-off-net10-root/B01 | 582.93 | 698.47 | 585.46 | 701.01 | 416.00 | 416.00 |
| Root | parent | tiering-off-net10-root/B02 | 580.49 | 695.75 | 583.03 | 698.27 | 416.00 | 416.00 |
| Root | parent | tiering-off-net10-root/B03 | 576.82 | 692.23 | 579.37 | 694.74 | 416.00 | 416.00 |
| Root | link | tiering-off-net10-root/B00 | 816.97 | 948.30 | 819.50 | 950.85 | 632.00 | 632.00 |
| Root | link | tiering-off-net10-root/B01 | 818.73 | 956.97 | 821.28 | 959.53 | 632.00 | 632.00 |
| Root | link | tiering-off-net10-root/B02 | 804.14 | 936.56 | 806.70 | 939.13 | 632.00 | 632.00 |
| Root | link | tiering-off-net10-root/B03 | 819.30 | 935.03 | 821.85 | 937.59 | 632.00 | 632.00 |
| NoListeners | parent | tiering-off-net10-nolisteners/B00 | 37.79 | 132.94 | 40.28 | 135.46 | 0.00 | 0.00 |
| NoListeners | parent | tiering-off-net10-nolisteners/B01 | 37.78 | 141.91 | 40.30 | 144.41 | 0.00 | 0.00 |
| NoListeners | parent | tiering-off-net10-nolisteners/B02 | 38.87 | 132.11 | 41.37 | 134.64 | 0.00 | 0.00 |
| NoListeners | parent | tiering-off-net10-nolisteners/B03 | 37.76 | 131.44 | 40.26 | 133.96 | 0.00 | 0.00 |
| NoListeners | link | tiering-off-net10-nolisteners/B00 | 38.27 | 131.86 | 40.77 | 134.36 | 0.00 | 0.00 |
| NoListeners | link | tiering-off-net10-nolisteners/B01 | 37.83 | 133.12 | 40.33 | 135.62 | 0.00 | 0.00 |
| NoListeners | link | tiering-off-net10-nolisteners/B02 | 37.81 | 131.11 | 40.32 | 133.64 | 0.00 | 0.00 |
| NoListeners | link | tiering-off-net10-nolisteners/B03 | 37.76 | 130.61 | 40.25 | 133.13 | 0.00 | 0.00 |
| AmbientParent | parent | tiering-off-net10-ambientparent/B00 | 667.97 | 792.31 | 670.49 | 794.83 | 432.00 | 432.00 |
| AmbientParent | parent | tiering-off-net10-ambientparent/B01 | 662.14 | 796.59 | 664.66 | 799.14 | 432.00 | 432.00 |
| AmbientParent | parent | tiering-off-net10-ambientparent/B02 | 679.05 | 793.65 | 681.59 | 796.20 | 432.00 | 432.00 |
| AmbientParent | parent | tiering-off-net10-ambientparent/B03 | 662.65 | 802.52 | 665.18 | 805.05 | 432.00 | 432.00 |
| AmbientParent | link | tiering-off-net10-ambientparent/B00 | 682.23 | 803.70 | 684.74 | 806.23 | 432.00 | 432.00 |
| AmbientParent | link | tiering-off-net10-ambientparent/B01 | 669.66 | 810.65 | 672.17 | 813.18 | 432.00 | 432.00 |
| AmbientParent | link | tiering-off-net10-ambientparent/B02 | 666.07 | 782.28 | 668.62 | 784.81 | 432.00 | 432.00 |
| AmbientParent | link | tiering-off-net10-ambientparent/B03 | 668.16 | 792.57 | 670.68 | 795.09 | 432.00 | 432.00 |

</details>

## .NET 10 application SDK sensitivity

Application TracerProvider with ParentBased(AlwaysOn) sampling for the recorded source; no exporters. The no-listener source remains unsubscribed.

| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ B/op |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 4 | 465.32 → 554.29 | 88.97 [48.37, 129.57] | 0.00 |
| Root | link | 4 | 606.83 → 694.90 | 88.07 [74.52, 101.61] | 0.00 |
| NoListeners | parent | 4 | 12.76 → 96.09 | 83.33 [82.18, 84.48] | 0.00 |
| NoListeners | link | 4 | 13.83 → 91.09 | 77.25 [73.00, 81.51] | 0.00 |
| CreateOnly | parent | 4 | 133.60 → 215.88 | 82.28 [73.85, 90.71] | 0.00 |
| CreateOnly | link | 4 | 285.91 → 347.05 | 61.13 [47.10, 75.16] | 0.00 |

<details>
<summary>Process ranges and raw Actual comparisons</summary>

Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction is a material fraction of the factory time.

| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | parent | 441.76–479.78 → 548.06–566.28 | 88.65 [47.70, 129.59] | 2.84–4.17 → 2.81–2.95 | 416.00 → 416.00 |
| Root | link | 602.07–615.16 → 684.73–711.61 | 88.47 [74.09, 102.85] | 2.86–3.04 → 2.94–4.50 | 632.00 → 632.00 |
| NoListeners | parent | 12.22–13.78 → 94.93–97.55 | 82.27 [80.32, 84.22] | 2.92–4.49 → 2.80–3.08 | 0.00 → 0.00 |
| NoListeners | link | 13.76–13.91 → 88.87–94.91 | 77.97 [74.53, 81.41] | 2.80–2.94 → 2.80–4.48 | 0.00 → 0.00 |
| CreateOnly | parent | 130.18–141.44 → 214.70–218.02 | 82.10 [73.27, 90.93] | 4.66–6.21 → 4.68–5.09 | 200.00 → 200.00 |
| CreateOnly | link | 278.01–296.76 → 345.23–349.99 | 61.20 [45.86, 76.53] | 5.12–6.79 → 5.11–7.33 | 416.00 → 416.00 |

</details>

<details>
<summary>All paired process means, with distinct cohort/block IDs</summary>

Values are rounded here; the linked source analysis preserves full precision and all iterations. A control-baseline process can appear in more than one comparison.

| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Baseline Actual | Candidate Actual | Baseline B/op | Candidate B/op |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root | parent | sdk-net10-root/B00 | 441.76 | 566.28 | 444.73 | 569.09 | 416.00 | 416.00 |
| Root | parent | sdk-net10-root/B01 | 462.57 | 553.05 | 465.53 | 556.00 | 416.00 | 416.00 |
| Root | parent | sdk-net10-root/B02 | 479.78 | 549.76 | 483.95 | 552.72 | 416.00 | 416.00 |
| Root | parent | sdk-net10-root/B03 | 477.16 | 548.06 | 480.00 | 550.98 | 416.00 | 416.00 |
| Root | link | sdk-net10-root/B00 | 615.16 | 711.61 | 618.02 | 716.11 | 632.00 | 632.00 |
| Root | link | sdk-net10-root/B01 | 602.62 | 696.74 | 605.66 | 699.70 | 632.00 | 632.00 |
| Root | link | sdk-net10-root/B02 | 602.07 | 684.73 | 605.05 | 687.67 | 632.00 | 632.00 |
| Root | link | sdk-net10-root/B03 | 607.46 | 686.51 | 610.33 | 689.46 | 632.00 | 632.00 |
| NoListeners | parent | sdk-net10-nolisteners/B00 | 13.78 | 97.55 | 16.71 | 100.63 | 0.00 | 0.00 |
| NoListeners | parent | sdk-net10-nolisteners/B01 | 12.26 | 94.93 | 16.75 | 97.85 | 0.00 | 0.00 |
| NoListeners | parent | sdk-net10-nolisteners/B02 | 12.77 | 95.54 | 16.70 | 98.34 | 0.00 | 0.00 |
| NoListeners | parent | sdk-net10-nolisteners/B03 | 12.22 | 96.34 | 16.71 | 99.14 | 0.00 | 0.00 |
| NoListeners | link | sdk-net10-nolisteners/B00 | 13.76 | 94.91 | 16.71 | 97.71 | 0.00 | 0.00 |
| NoListeners | link | sdk-net10-nolisteners/B01 | 13.91 | 90.60 | 16.71 | 94.72 | 0.00 | 0.00 |
| NoListeners | link | sdk-net10-nolisteners/B02 | 13.76 | 88.87 | 16.70 | 93.35 | 0.00 | 0.00 |
| NoListeners | link | sdk-net10-nolisteners/B03 | 13.90 | 89.98 | 16.70 | 92.91 | 0.00 | 0.00 |
| CreateOnly | parent | sdk-net10-createonly/B00 | 130.35 | 214.99 | 135.02 | 220.08 | 200.00 | 200.00 |
| CreateOnly | parent | sdk-net10-createonly/B01 | 132.44 | 218.02 | 137.09 | 223.10 | 200.00 | 200.00 |
| CreateOnly | parent | sdk-net10-createonly/B02 | 141.44 | 215.81 | 146.56 | 220.49 | 200.00 | 200.00 |
| CreateOnly | parent | sdk-net10-createonly/B03 | 130.18 | 214.70 | 136.39 | 219.79 | 200.00 | 200.00 |
| CreateOnly | link | sdk-net10-createonly/B00 | 296.76 | 345.23 | 303.36 | 350.34 | 416.00 | 416.00 |
| CreateOnly | link | sdk-net10-createonly/B01 | 283.13 | 349.99 | 288.26 | 356.39 | 416.00 | 416.00 |
| CreateOnly | link | sdk-net10-createonly/B02 | 278.01 | 345.43 | 284.79 | 350.61 | 416.00 | 416.00 |
| CreateOnly | link | sdk-net10-createonly/B03 | 285.77 | 347.53 | 291.01 | 354.87 | 416.00 | 416.00 |

</details>

## .NET 10 link-aware sampler supplement

Separate LinkSamplingBenchmarks class: the sampler enumerates links and records only when it sees the incoming trace/span IDs. Both manual and automatic cases validate equivalent recorded activities. These results are kept separate from the primary listener that does not inspect recorded-source links.

| Workload | Comparison | Blocks | Baseline → candidate ns/op | Δ ns/op [95% CI] | Δ B/op |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | link | 4 | 556.65 → 647.69 | 91.04 [72.04, 110.04] | 0.00 |
| RootExistingLink | link | 4 | 635.16 → 977.33 | 342.17 [324.33, 360.01] | 160.00 |

<details>
<summary>Process ranges and raw Actual comparisons</summary>

Ranges are minimum–maximum process means, rather than iteration ranges. Overhead ranges use each process's median empty-loop overhead. Raw Actual deltas include that loop overhead; they are useful when subtraction is a material fraction of the factory time.

| Workload | Comparison | Result process-mean ranges: baseline → candidate | Raw Actual Δ ns/op [95% CI] | Overhead median ranges: baseline → candidate | B/op ranges: baseline → candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| Root | link | 541.99–568.29 → 640.10–659.72 | 91.43 [71.72, 111.14] | 2.96–4.46 → 2.83–4.89 | 664.00 → 664.00 |
| RootExistingLink | link | 625.50–639.21 → 968.40–994.89 | 343.06 [323.46, 362.66] | 2.75–4.80 → 4.18–4.89 | 728.00 → 888.00 |

</details>

<details>
<summary>All paired process means, with distinct cohort/block IDs</summary>

Values are rounded here; the linked source analysis preserves full precision and all iterations. A control-baseline process can appear in more than one comparison.

| Workload | Comparison | Cohort/block | Baseline Result | Candidate Result | Baseline Actual | Candidate Actual | Baseline B/op | Candidate B/op |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Root | link | link-sampling-root-net10/B00 | 541.99 | 643.27 | 544.95 | 646.10 | 664.00 | 664.00 |
| Root | link | link-sampling-root-net10/B01 | 568.29 | 659.72 | 572.46 | 663.89 | 664.00 | 664.00 |
| Root | link | link-sampling-root-net10/B02 | 550.42 | 647.68 | 553.38 | 652.57 | 664.00 | 664.00 |
| Root | link | link-sampling-root-net10/B03 | 565.92 | 640.10 | 570.37 | 644.32 | 664.00 | 664.00 |
| RootExistingLink | link | link-sampling-existing-net10/B00 | 639.21 | 975.95 | 644.01 | 980.84 | 728.00 | 888.00 |
| RootExistingLink | link | link-sampling-existing-net10/B01 | 625.50 | 970.09 | 628.38 | 974.58 | 728.00 | 888.00 |
| RootExistingLink | link | link-sampling-existing-net10/B02 | 637.71 | 968.40 | 642.14 | 972.57 | 728.00 | 888.00 |
| RootExistingLink | link | link-sampling-existing-net10/B03 | 638.23 | 994.89 | 640.98 | 999.75 | 728.00 | 888.00 |

</details>

## Measured target versions

| Requested runtime | Target framework | DiagnosticSource file version | Application TracerProvider SDK assembly version |
| --- | --- | --- | --- |
| net10.0 | .NET 10.0.14 | 10.0.1426.52326 | 1.0.0.0 |
| net10.0 | .NET 10.0.14 | 10.0.1426.52326 | none |
| net8.0 | .NET 8.0.33 | 10.0.25.52411 | none |
| net9.0 | .NET 9.0.22 | 10.0.25.52411 | none |

## Workload definitions

| Workload | Measured work |
| --- | --- |
| Root | StartActivity with an ActivityContext parent argument and optional links; create, start, and dispose. |
| RootEmptyLinks | The root factory with an explicitly empty links collection in automatic mode; the manual link control supplies its cached incoming link. |
| RootExistingLink | The root factory with one unrelated existing link; the manual link control supplies both links in a cached collection. |
| RootAlreadyLinked | The incoming link is already supplied; automatic link mode must avoid adding it again. |
| NoListeners | Ordinary StartActivity("job") on a source with no listeners; returns null. |
| Dropped | A listener returns ActivitySamplingResult.None without enumerating links; no Activity is created. |
| DropReadingLinks | A listener enumerates the existing/incoming links, then returns None. |
| AmbientParent | Ordinary StartActivity("job") with an existing Activity.Current; preserve that parent. |
| SuppliedContext | StartActivity with an explicit unrelated ActivityContext parent; preserve it. |
| SuppliedParentId | StartActivity with an explicit unrelated W3C parent-ID string; preserve it. |
| SuppliedEmptyParentId | StartActivity with an explicit empty parent-ID string; preserve the caller's root choice. |
| CreateOnly | CreateActivity returns an unstarted Activity; its construction and sampling are measured, without Start/Stop. |
| CreateThenStart | CreateActivity, then Start, then dispose. |
| PropagationOnly | A listener returns PropagationData; create/start/dispose without requesting recorded data. |

Manual controls use a parsed remote parent or immutable cached link collections. Automatic profiles receive startup environment context. Parent-bearing root overloads are matched between manual and automatic cases. Existing-link controls cache the complete equivalent list; they do not rebuild it inside the timed call.

## Interpretation limits

- The configured warmup is 10 seconds of the actual target method plus 40 BenchmarkDotNet warmup iterations; measurement uses 20 iterations with a configured 250 ms target; actual durations may be shorter and are retained, with DontRemove. Startup, extraction, provider construction, and asynchronous ReJIT readiness are outside the measured operation.
- Each mode has four fresh processes per checkpoint. Four-block intervals have limited precision; repeated-workload aggregations retain both cohorts and every process, including stable slower regimes. These nominal pointwise intervals assume approximately normal independent block differences and have no multiplicity adjustment.
- This is a single Linux KVM host using CPU3 affinity and concurrent workstation GC. Its SMT sibling CPU11 is monitored, together with steal time, CPU pressure, and cgroup throttling. Affinity does not guarantee exclusive physical-host CPU or fixed frequency. Results do not establish server-GC, other-platform, or production latency guarantees.
- Parent mode can avoid creating a new trace ID; link mode keeps a new trace. Simple-overload, no-agent, and cross-runtime differences can include runtime/JIT/code-layout work. Treat these as measured use cases rather than a universal cost for the hook. Empty-loop subtraction is especially material for the no-listener controls.
- MemoryDiagnoser B/op is a per-process report, not a distribution of per-iteration allocation observations. The report shows allocation deltas and process ranges; it does not infer an allocation confidence interval.
- The primary listener returns fixed sampling decisions. The SDK and link-aware sampler subsets add representative sampling paths without exporters; they do not model all SDK/exporter/application configurations.
- Source and binary provenance has the exact scope recorded in each checkpoint analysis. This report does not expand those claims. Discarded pilots and aborted multi-method phases are excluded by an explicit checkpoint allowlist.

## Checkpoint coverage and source analyses

Cohort names below form part of every block ID. Original and repeat block numbers are never merged as the same process. The process/comparison files retain the measurements and within-cohort statistics used here.

| Checkpoint / cohort | Status | Processes | Source provenance | Analyses |
| --- | --- | ---: | --- | --- |
| [no-listener-net10](results/no-listener-net10/run.json) | analyzed | 16/16 | legacy_current_source_unbound | [processes](results/no-listener-net10/analysis/processes.json), [comparisons](results/no-listener-net10/analysis/comparisons.json) |
| [activity-net10-root](results/activity-net10-root/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-root/analysis/processes.json), [comparisons](results/activity-net10-root/analysis/comparisons.json) |
| [activity-net10-rootemptylinks](results/activity-net10-rootemptylinks/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-rootemptylinks/analysis/processes.json), [comparisons](results/activity-net10-rootemptylinks/analysis/comparisons.json) |
| [activity-net10-rootexistinglink](results/activity-net10-rootexistinglink/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-rootexistinglink/analysis/processes.json), [comparisons](results/activity-net10-rootexistinglink/analysis/comparisons.json) |
| [activity-net10-rootalreadylinked](results/activity-net10-rootalreadylinked/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-rootalreadylinked/analysis/processes.json), [comparisons](results/activity-net10-rootalreadylinked/analysis/comparisons.json) |
| [activity-net10-dropped](results/activity-net10-dropped/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-dropped/analysis/processes.json), [comparisons](results/activity-net10-dropped/analysis/comparisons.json) |
| [activity-net10-dropreadinglinks](results/activity-net10-dropreadinglinks/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-dropreadinglinks/analysis/processes.json), [comparisons](results/activity-net10-dropreadinglinks/analysis/comparisons.json) |
| [activity-net10-ambientparent](results/activity-net10-ambientparent/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-ambientparent/analysis/processes.json), [comparisons](results/activity-net10-ambientparent/analysis/comparisons.json) |
| [activity-net10-suppliedcontext](results/activity-net10-suppliedcontext/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-suppliedcontext/analysis/processes.json), [comparisons](results/activity-net10-suppliedcontext/analysis/comparisons.json) |
| [activity-net10-suppliedparentid](results/activity-net10-suppliedparentid/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-suppliedparentid/analysis/processes.json), [comparisons](results/activity-net10-suppliedparentid/analysis/comparisons.json) |
| [activity-net10-suppliedemptyparentid](results/activity-net10-suppliedemptyparentid/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-suppliedemptyparentid/analysis/processes.json), [comparisons](results/activity-net10-suppliedemptyparentid/analysis/comparisons.json) |
| [activity-net10-createonly](results/activity-net10-createonly/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-createonly/analysis/processes.json), [comparisons](results/activity-net10-createonly/analysis/comparisons.json) |
| [activity-net10-createthenstart](results/activity-net10-createthenstart/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-createthenstart/analysis/processes.json), [comparisons](results/activity-net10-createthenstart/analysis/comparisons.json) |
| [activity-net10-propagationonly](results/activity-net10-propagationonly/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net10-propagationonly/analysis/processes.json), [comparisons](results/activity-net10-propagationonly/analysis/comparisons.json) |
| [activity-net8-root](results/activity-net8-root/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net8-root/analysis/processes.json), [comparisons](results/activity-net8-root/analysis/comparisons.json) |
| [activity-net8-nolisteners](results/activity-net8-nolisteners/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net8-nolisteners/analysis/processes.json), [comparisons](results/activity-net8-nolisteners/analysis/comparisons.json) |
| [activity-net8-dropped](results/activity-net8-dropped/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net8-dropped/analysis/processes.json), [comparisons](results/activity-net8-dropped/analysis/comparisons.json) |
| [activity-net8-ambientparent](results/activity-net8-ambientparent/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net8-ambientparent/analysis/processes.json), [comparisons](results/activity-net8-ambientparent/analysis/comparisons.json) |
| [activity-net8-suppliedcontext](results/activity-net8-suppliedcontext/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net8-suppliedcontext/analysis/processes.json), [comparisons](results/activity-net8-suppliedcontext/analysis/comparisons.json) |
| [activity-net8-createonly](results/activity-net8-createonly/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net8-createonly/analysis/processes.json), [comparisons](results/activity-net8-createonly/analysis/comparisons.json) |
| [activity-net9-root](results/activity-net9-root/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net9-root/analysis/processes.json), [comparisons](results/activity-net9-root/analysis/comparisons.json) |
| [activity-net9-nolisteners](results/activity-net9-nolisteners/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net9-nolisteners/analysis/processes.json), [comparisons](results/activity-net9-nolisteners/analysis/comparisons.json) |
| [activity-net9-dropped](results/activity-net9-dropped/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net9-dropped/analysis/processes.json), [comparisons](results/activity-net9-dropped/analysis/comparisons.json) |
| [activity-net9-ambientparent](results/activity-net9-ambientparent/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net9-ambientparent/analysis/processes.json), [comparisons](results/activity-net9-ambientparent/analysis/comparisons.json) |
| [activity-net9-suppliedcontext](results/activity-net9-suppliedcontext/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net9-suppliedcontext/analysis/processes.json), [comparisons](results/activity-net9-suppliedcontext/analysis/comparisons.json) |
| [activity-net9-createonly](results/activity-net9-createonly/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-net9-createonly/analysis/processes.json), [comparisons](results/activity-net9-createonly/analysis/comparisons.json) |
| [controls-net10-root](results/controls-net10-root/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/controls-net10-root/analysis/processes.json), [comparisons](results/controls-net10-root/analysis/comparisons.json) |
| [controls-net10-nolisteners](results/controls-net10-nolisteners/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/controls-net10-nolisteners/analysis/processes.json), [comparisons](results/controls-net10-nolisteners/analysis/comparisons.json) |
| [tiering-off-net10-root](results/tiering-off-net10-root/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/tiering-off-net10-root/analysis/processes.json), [comparisons](results/tiering-off-net10-root/analysis/comparisons.json) |
| [tiering-off-net10-nolisteners](results/tiering-off-net10-nolisteners/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/tiering-off-net10-nolisteners/analysis/processes.json), [comparisons](results/tiering-off-net10-nolisteners/analysis/comparisons.json) |
| [tiering-off-net10-ambientparent](results/tiering-off-net10-ambientparent/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/tiering-off-net10-ambientparent/analysis/processes.json), [comparisons](results/tiering-off-net10-ambientparent/analysis/comparisons.json) |
| [sdk-net10-root](results/sdk-net10-root/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/sdk-net10-root/analysis/processes.json), [comparisons](results/sdk-net10-root/analysis/comparisons.json) |
| [sdk-net10-nolisteners](results/sdk-net10-nolisteners/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/sdk-net10-nolisteners/analysis/processes.json), [comparisons](results/sdk-net10-nolisteners/analysis/comparisons.json) |
| [sdk-net10-createonly](results/sdk-net10-createonly/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/sdk-net10-createonly/analysis/processes.json), [comparisons](results/sdk-net10-createonly/analysis/comparisons.json) |
| [no-listener-repeat-net10](results/no-listener-repeat-net10/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/no-listener-repeat-net10/analysis/processes.json), [comparisons](results/no-listener-repeat-net10/analysis/comparisons.json) |
| [activity-repeat-net10-root](results/activity-repeat-net10-root/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-repeat-net10-root/analysis/processes.json), [comparisons](results/activity-repeat-net10-root/analysis/comparisons.json) |
| [activity-repeat-net10-ambientparent](results/activity-repeat-net10-ambientparent/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-repeat-net10-ambientparent/analysis/processes.json), [comparisons](results/activity-repeat-net10-ambientparent/analysis/comparisons.json) |
| [activity-repeat-net10-dropped](results/activity-repeat-net10-dropped/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-repeat-net10-dropped/analysis/processes.json), [comparisons](results/activity-repeat-net10-dropped/analysis/comparisons.json) |
| [activity-repeat-net10-suppliedcontext](results/activity-repeat-net10-suppliedcontext/run.json) | analyzed | 16/16 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/activity-repeat-net10-suppliedcontext/analysis/processes.json), [comparisons](results/activity-repeat-net10-suppliedcontext/analysis/comparisons.json) |
| [link-sampling-root-net10](results/link-sampling-root-net10/run.json) | analyzed | 8/8 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/link-sampling-root-net10/analysis/processes.json), [comparisons](results/link-sampling-root-net10/analysis/comparisons.json) |
| [link-sampling-existing-net10](results/link-sampling-existing-net10/run.json) | analyzed | 8/8 | captured_binary_and_csharp_sources_bound_by_helper | [processes](results/link-sampling-existing-net10/analysis/processes.json), [comparisons](results/link-sampling-existing-net10/analysis/comparisons.json) |

Reproduce the report with `taskset -c 1 python3 report.py`; `--require-complete` exits unsuccessfully until every planned checkpoint has a valid completed analysis.
