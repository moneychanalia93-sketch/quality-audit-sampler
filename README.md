# quality-audit-sampler

A small command-line tool for quality audits. It picks a fair random sample of work items to check, loads the audit results, and reports the pass rate and error rate with an honest margin of error.

It uses only the Python standard library (`random`, `math`, `csv`, `sqlite3`, `argparse`, `unittest`). There is nothing to install. Python 3.13 was used; any recent Python 3 should work.

> Built with AI assistance (Kiro). I designed the rules, reviewed the code, and ran the tests.
> This is a learning project. **All data is fake** (made by the `seed` command). It has not been used in production.

## What it does

- `seed`: writes 2,000 fake work items (5 workflows, 20 workers, 10 days). Three workers are secretly a bit worse than the rest.
- `sample`: picks N items to audit. Three modes: `simple` (random), `stratified` (each workflow gets its fair share) and `focus` (only workers with a recent failed audit). A seed number makes every draw repeatable. An item is never picked twice in one draw, and items that already have an audit are skipped.
- `record`: loads audit results (pass or fail, plus a reason code for a fail) from a CSV. Bad rows are counted and shown, not hidden.
- `report`: pass rate and error rate overall, per workflow and per worker, each with a 95% interval and a flag when the pass rate is below a target.
- `sample-size`: how many audits you need for a margin of error you choose, with the formula and the working.
- `simulate`: repeats the sampling 1,000 times on the fake data, where the true rate is known, and counts how often the 95% interval contained the truth.
- `pretend-audit`: fills in a sample CSV from the fake data's hidden truth, so you can try the whole cycle without a human auditor.

## Run it (3 commands)

Run these from the project folder. If `python` is not on your PATH, use `py` or the full path to `python.exe`.

```powershell
python -m sampler seed                      # creates audit.db with 2,000 fake items
python -m sampler simulate                  # checks the method 1,000 times
python -m unittest discover -s tests -t .   # runs the tests
```

Real output of the first command:

```
Wrote 2000 fake items to audit.db (seed 42).
Hidden truth, used only by `simulate` and `pretend-audit`: 82 items have an error (4.1%).
```

Real output of the second command:

```
Fake population: 2000 items, true pass rate 95.90% (known, because we made the data).
Each row repeats the draw 1000 times and counts how often the 95% interval held the true rate.

  method       audits   held the truth   avg width
  simple           30            96.9%       16.4%
  simple          200            96.3%        5.6%
  stratified       30            97.1%       16.4%
  stratified      200            96.2%        5.6%
```

The interval held the truth 96% to 97% of the time. That is near 95%, a little above it. See "What the simulation shows" below.

## One audit cycle

Four commands, in order. Output below is real, run right after `seed`.

```powershell
python -m sampler sample --n 300 --mode stratified   # 1. pick 300 items -> sample.csv
python -m sampler pretend-audit sample.csv           # 2. a person would audit them; here we fake it -> results.csv
python -m sampler record results.csv                 # 3. load the results
python -m sampler report                             # 4. the numbers
```

```
Picked 300 items (mode stratified, seed 1) -> sample.csv
  address_check    126
  data_entry        37
  invoice_match     76
  photo_label       41
  refund_review     20
Pretend auditor filled in 300 rows -> results.csv
Recorded 300 audits. Rejected 0 bad rows.
```

`sample.csv` has the columns `item_id,workflow,worker,day,result,reason`. The last two are empty. An auditor fills in `result` (`pass` or `fail`) and, for a fail, `reason` (one of `wrong_value`, `missing_field`, `wrong_category`, `late_entry`, `other`). Then `record` loads the file.

The report:

```
Audited 300 of 2000 items (focus audits not counted here: 0).
Target pass rate: 95.0%

OVERALL: pass rate 97.7% (293 of 300), error rate 2.3%
  We are 95% sure the true pass rate is between 95.3% and 98.9%.
  We are 95% sure the true error rate is between 1.1% and 4.7%.

BY WORKFLOW
  name            audits  passed  pass rate   95% interval     flag
  address_check      126     122      96.8%    92.1% to  98.8%  ok
  data_entry          37      35      94.6%    82.3% to  98.5%  BELOW TARGET
  invoice_match       76      76     100.0%    95.2% to 100.0%  ok
  photo_label         41      40      97.6%    87.4% to  99.6%  ok
  refund_review       20      20     100.0%    83.9% to 100.0%  ok (only 20 audits: too few to say)

BY WORKER
  name            audits  passed  pass rate   95% interval     flag
  W01                 13      12      92.3%    66.7% to  98.6%  BELOW TARGET (only 13 audits: too few to say)
  W02                 18      18     100.0%    82.4% to 100.0%  ok (only 18 audits: too few to say)
  W03                 16      16     100.0%    80.6% to 100.0%  ok (only 16 audits: too few to say)
  W04                 13      13     100.0%    77.2% to 100.0%  ok (only 13 audits: too few to say)
  W05                 18      16      88.9%    67.2% to  96.9%  BELOW TARGET (only 18 audits: too few to say)
  W06                  9       9     100.0%    70.1% to 100.0%  ok (only 9 audits: too few to say)
  W07                  9       9     100.0%    70.1% to 100.0%  ok (only 9 audits: too few to say)
  W08                 17      17     100.0%    81.6% to 100.0%  ok (only 17 audits: too few to say)
  W09                 13      13     100.0%    77.2% to 100.0%  ok (only 13 audits: too few to say)
  W10                  5       5     100.0%    56.6% to 100.0%  ok (only 5 audits: too few to say)
  W11                 15      15     100.0%    79.6% to 100.0%  ok (only 15 audits: too few to say)
  W12                 19      18      94.7%    75.4% to  99.1%  BELOW TARGET (only 19 audits: too few to say)
  W13                 21      21     100.0%    84.5% to 100.0%  ok (only 21 audits: too few to say)
  W14                 19      19     100.0%    83.2% to 100.0%  ok (only 19 audits: too few to say)
  W15                 14      14     100.0%    78.5% to 100.0%  ok (only 14 audits: too few to say)
  W16                 13      13     100.0%    77.2% to 100.0%  ok (only 13 audits: too few to say)
  W17                 15      13      86.7%    62.1% to  96.3%  BELOW TARGET (only 15 audits: too few to say)
  W18                 18      17      94.4%    74.2% to  99.0%  BELOW TARGET (only 18 audits: too few to say)
  W19                 19      19     100.0%    83.2% to 100.0%  ok (only 19 audits: too few to say)
  W20                 16      16     100.0%    80.6% to 100.0%  ok (only 16 audits: too few to say)
```

What this shows, honestly:

- The overall result is good. The true error rate in the fake data is 4.1% (the `seed` output above), and the report's interval for it (1.1% to 4.7%) contains it.
- With 300 audits spread over 20 workers, each worker has only 5 to 21 audits. Every worker line carries the "too few to say" warning, and the intervals are wide (for example W17: 62.1% to 96.3%).
- Of the three workers who are secretly worse (W03, W11, W17), only W17 is flagged. W03 and W11 got lucky samples with no failures. W01, W05, W12 and W18 are flagged because of one or two failures, although they are not among the worse workers. A small sample cannot tell these cases apart. That is the point of the warning.

### Focus mode

After audits exist, `focus` picks only from workers who had a failed audit on an item from the last 3 days of data (change it with `--recent-days`):

```powershell
python -m sampler sample --n 40 --mode focus --out focus.csv
python -m sampler pretend-audit focus.csv --out focus_results.csv
python -m sampler record focus_results.csv --focus
```

```
Focus workers: W05, W12, W17
Picked 40 items (mode focus, seed 1) -> focus.csv
  (a count per workflow follows, left out here)
Recorded 40 audits. Rejected 0 bad rows.
```

Use `--focus` when you record these results. A focus sample looks at suspect workers on purpose, so it is not a fair picture of everyone. Audits recorded with `--focus` are kept out of the overall, per-workflow and per-worker rates, and the report says how many were left out.

### Bad rows

`record` checks every row. A bad row is counted and skipped; the good rows are still saved. Real output for a file with six rows (item 1 already appears once above it, 99999 does not exist):

```
Recorded 2 audits. Rejected 4 bad rows.
  line 4: result must be pass or fail
  line 5: a fail needs a reason code: wrong_value, missing_field, wrong_category, late_entry, other
  line 6: unknown item
  line 7: item already audited
```

## How to choose the number of audits

```powershell
python -m sampler sample-size --margin 0.05
```

```
Audits needed for a margin of error of 5 percentage points (95% confidence)

Formula:  n = z^2 * p * (1 - p) / margin^2
Where:    z = 1.96 (95%), p = 0.5 (our guess of the rate; 0.5 is the safest),
          margin = 0.05
Worked:   n = 1.96^2 * 0.5 * (1 - 0.5) / 0.05^2
            = 3.8416 * 0.2500 / 0.002500
            = 384.16, rounded UP to 385 audits
```

If you expect a rate near 5%, say so with `--p 0.05`. You then need fewer audits: `--margin 0.03 --p 0.05` gives 203.

## How it works, in plain words

**A random sample.** You cannot check every item, so you check a few chosen by chance. Every item has the same chance of being picked, so the sample is not shaped by what is easy or interesting to check. `random.Random(seed).sample(...)` does the pick. The seed makes the "chance" repeatable: the same seed on the same items gives the same sample.

**A stratified sample.** If a workflow is only 8% of the items, a random sample of 20 might contain none of it. Stratified sampling gives each workflow a share of the draw in proportion to its size, then picks at random inside each. Example with three workflows of 50, 30 and 20 items and a draw of 10: the shares are 5, 3 and 2. When shares do not come out whole (3.5, 2.1 and 0.4 for a draw of 6), each workflow first gets the rounded-down number (3, 2, 0). The places left over go to the biggest cut-off fractions (the 0.5 wins), so the quotas always add up to exactly the draw size.

**The interval.** One sample gives one pass rate, for example 90 passes in 100 audits = 90%. A different sample would give a slightly different number. The Wilson interval gives a low and a high number that the true rate probably sits between. For 90 of 100:

```
p = 0.9, z = 1.96, n = 100
centre = (p + z^2 / 2n) / (1 + z^2 / n) = (0.9 + 0.0192) / 1.0384 = 0.8852
half   = z * sqrt(p(1-p)/n + z^2/4n^2) / (1 + z^2 / n) = 1.96 * 0.03156 / 1.0384 = 0.0596
interval = 0.8852 - 0.0596 to 0.8852 + 0.0596 = 82.6% to 94.5%
```

"We are 95% sure the true pass rate is between 82.6% and 94.5%." That sentence is plain-words shorthand. Exactly, it means: if you repeated the whole audit many times, about 95 of every 100 intervals built this way would contain the true rate. The `simulate` command measures that claim.

**Why a small sample is shaky.** Same 90% pass rate, but 9 passes in 10 audits: the interval is 59.6% to 98.2%. Ten audits cannot say much. `report` adds a warning when a group has fewer than 30 audits (`MIN_AUDITS` in `sampler/stats.py`; the 30 is a common rule of thumb, not a law).

**The flag.** A workflow or worker is flagged `BELOW TARGET` when its pass rate is under the target (default 95%, change with `--target`). The flag looks only at the pass rate. The interval and the small-sample warning tell you how much to trust it.

## What the simulation shows

`simulate` builds the fake data, so it knows the true pass rate (95.90%). It draws 200 items (or 30), audits them perfectly, builds the 95% interval, and checks whether the true rate is inside. It does this 1,000 times for each row of the table and counts. The interval held the truth 96.2% to 97.1% of the time.

Why a little above 95%? I believe two things: we sample without replacement (200 of 2,000 is 10% of the items), and the Wilson formula does not take that into account, which makes intervals slightly too wide. Also, with few audits the number of failures moves in whole steps, so coverage can sit above or below 95%. Each result is itself a count of 1,000 runs, so it is accurate to roughly 1 percentage point. I have not tested other data or other sample sizes beyond the table.

The interval is much narrower with 200 audits (5.6% wide) than with 30 (16.4% wide). Stratified and simple sampling give the same width here, because in this fake data the error rate does not differ by workflow, so stratifying gains nothing.

## Limits

- The data is fake. The error rates (3.5% for most workers, 9% for three) were chosen by me. Nothing here says how any real operation performs.
- The method assumes items are independent: one item being wrong does not make another more likely. Real work often breaks that rule (the same worker, the same bad batch).
- It assumes the audit itself is right. A wrong audit result is counted as truth.
- A simple random or stratified sample is only fair if the list of items you sample from is complete. Items missing from the list can never be picked.
- The interval treats the stratified sample like a simple one. That is slightly conservative, not wrong. A full stratified estimate is not built.
- `sample-size` uses the simple (Wald) formula, while `report` uses Wilson. They can differ for rates near 0% or 100%.
- No finite-population correction (see the simulation note).
- With 20 workers and a few hundred audits, the per-worker lines are shaky. The tool says so, but it does not fix it. More audits or a longer time window would.
- "Recent failures" in `focus` mode means a failed audit on an item from the last N days of the data. It is my definition, kept simple.
- Same seed gives the same sample on the same Python version. Different Python versions may use a different random algorithm.
- Tests cover the behavior listed here. There is no performance testing; this is small data in SQLite.

## Run the tests

```powershell
python -m unittest discover -s tests -t .
```

Real result: `Ran 52 tests ... OK`. They cover seeding (repeatable, shape of the data), sampling (sizes, no duplicates, repeatable, stratified shares add up, focus mode), recording (bad rows counted), the maths (Wilson interval and sample size against hand-computed numbers, small-sample warning), the report, the command line, and the simulation.

## Files

```
sampler/stats.py       the maths: Wilson interval, sample size, sentences, flags
sampler/seed.py        makes the fake items
sampler/db.py          all the SQL (two tables: items and audits)
sampler/sampling.py    simple, stratified and focus sampling
sampler/records.py     CSV in and out, row checks, the pretend auditor
sampler/report.py      builds the report text
sampler/simulate.py    the 1,000-repeat check
sampler/cli.py         the commands (argparse)
tests/                 unittest tests
```

## License

MIT. See `LICENSE`.
