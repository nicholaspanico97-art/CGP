# Scope — a window into the simulation

`scope.html` renders a full run: a month scrubber driving sector tiles, a
per-lab time series, each lab's capability profile across all eight domains,
the segmented market, and a lab state table.

## Regenerate

```
python3 -m sim.export run.json
python3 -c "d=open('run.json').read(); open('viewer/rundata.js','w').write('window.RUN='+d+';')"
```

Then open `viewer/scope.html` with `rundata.js` beside it, or publish both
together. The page reads `window.RUN` and needs nothing else — no libraries,
no network.

Nothing in the viewer computes anything. Every number on the page came out
of `sim/`, so if something looks wrong, the model is wrong.
