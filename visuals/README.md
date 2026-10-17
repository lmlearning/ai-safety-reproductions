# How the publication graphs were made

The dashboard and standardized study charts visualize recorded programme results. They do not run new experiments or reassess paper validity.

The [chart data](metrics.json) identify the source publication commit, source files, original central comparison families and study-specific limits. Every study also has a compact `visuals/summary.json` alongside its PNG and SVG chart. The [graphics build record](BUILD.json) lists output hashes and the plotting-library version.

## Reading the graphs

- The main dashboard counts reproduction outcomes, computational routes and selection windows. Its near-success total includes eight bounded or precision-supported cases and one separately qualified case with material exceptions.
- Citation counts are the retained initial selection observations. Semantic Scholar and OpenAlex are identified separately and were not combined. The chart ranks attention recorded during selection, not scientific quality or current impact.
- Each study chart shows its original central target checks. A match means agreement within that study's original comparison criteria, which may include numerical or Monte Carlo tolerances; it does not mean literal equality. Target families and denominators differ across studies. They are not a common score, and no pooled success percentage is calculated.
- The near-success label uses the declared bounded or qualified interpretation. The chart preserves the earlier strict comparison counts alongside that label. Input validation, supporting displays and independent audit counts are not silently added to central target denominators.
- Unmatched checks record what this programme did not reproduce within its constraints. They do not establish that the paper or its conclusions are invalid. Work outside the attempted scope was untested.

## Render the graphs again

Use Python 3.11 or later and install the optional dependencies in [requirements-visuals.txt](../tools/requirements-visuals.txt), then run from the repository root:

```console
python tools/render_visuals.py
```

To render one study chart:

```console
python tools/render_visuals.py --study P041
```

The renderer reads the recorded JSON and writes publication images. It does not download scientific data, call model APIs or execute a reproduction. PNG is used in the READMEs for consistent GitHub display; SVG is included for resizing or reuse. The source, chart metadata and original documentation use the repository's MIT licence, subject to its existing third-party exceptions.
