# Repository Analysis Tool

Analyze local or remote Git repositories and produce practical engineering metadata: authored lines of code, languages, frameworks, Git activity, contributors, tokens, duplication, security findings, and a repository rating. It can also evaluate a group of repositories against acceptance rules.

## Install

Requirements: Python 3, Git, and [SCC](https://github.com/boyter/scc) **3.7.0 or newer**.

```bash
git clone <this-repository-url>
cd repo_analysis_metadata_script
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Install `scc` so it is available on your `PATH`, or place its executable beside `Repo_analysis_tool.py`. Confirm the setup:

```bash
scc --version
python Repo_analysis_tool.py --help
```

Optional: copy `env.example` to `.env` and add a GitHub, GitLab, or Bitbucket token. Tokens enable API enrichment and are required for private remote repositories.

## Run

Analyze a local repository:

```bash
python Repo_analysis_tool.py -i /path/to/repository
```

Analyze a remote repository or a specific branch:

```bash
python Repo_analysis_tool.py -i https://github.com/redis/redis.git --branch unstable
```

Useful options:

```bash
# Fast structural pre-check only
python Repo_analysis_tool.py -i /path/to/repository --mode stage1

# Choose where reports are written
python Repo_analysis_tool.py -i /path/to/repository -o ./reports

# Analyze projects listed in projects.csv
python Repo_analysis_tool.py --projects projects.csv
```

Use `projects.example.csv` as the starting point for project input, or create one interactively:

```bash
python Repo_analysis_tool.py --project-wizard
```

## Docker

Build the self-contained CLI image (Python, Git, and SCC are included):

```bash
docker build -t repository-analysis-tool .
docker run --rm \
  -v /path/to/repository:/workspace/target:ro \
  -v "$(pwd)/outputs:/workspace/outputs" \
  repository-analysis-tool \
  --input /workspace/target --output-dir /workspace/outputs
```

With Docker Compose, set `ANALYSIS_TARGET` to the repository you want to analyze, then run:

```bash
ANALYSIS_TARGET=/path/to/repository docker compose run --rm analyzer
```

The CI workflow compiles the Python source, builds the image, and runs a CLI smoke test for every pull request and push to `main`.

### Usage

Command line usage of `scc` is designed to be as simple as possible.
Full details can be found in `scc --help` or `scc -h`. Note that the below reflects the state of master not a release, as such
features listed below may be missing from your installation.

```text
Sloc, Cloc and Code. Count lines of code in a directory with complexity estimation.
Version 3.5.0 (beta)
Ben Boyter <ben@boyter.org> + Contributors

Usage:
  scc [flags] [files or directories]

Flags:
      --avg-wage int                       average wage value used for basic COCOMO calculation (default 56286)
      --binary                             disable binary file detection
      --by-file                            display output for every file
  -m, --character                          calculate max and mean characters per line
      --ci                                 enable CI output settings where stdout is ASCII
      --cocomo-project-type string         change COCOMO model type [organic, semi-detached, embedded, "custom,1,1,1,1"] (default "organic")
      --count-as string                    count extension as language [e.g. jsp:htm,chead:"C Header" maps extension jsp to html and chead to C Header]
      --count-ignore                       set to allow .gitignore and .ignore files to be counted
      --currency-symbol string             set currency symbol (default "$")
      --debug                              enable debug output
      --directory-walker-job-workers int   controls the maximum number of workers which will walk the directory tree (default 8)
  -a, --dryness                            calculate the DRYness of the project (implies --uloc)
      --eaf float                          the effort adjustment factor derived from the cost drivers (1.0 if rated nominal) (default 1)
      --exclude-dir strings                directories to exclude (default [.git,.hg,.svn])
  -x, --exclude-ext strings                ignore file extensions (overrides include-ext) [comma separated list: e.g. go,java,js]
  -n, --exclude-file strings               ignore files with matching names (default [package-lock.json,Cargo.lock,yarn.lock,pubspec.lock,Podfile.lock,pnpm-lock.yaml])
      --file-gc-count int                  number of files to parse before turning the GC on (default 10000)
      --file-list-queue-size int           the size of the queue of files found and ready to be read into memory (default 8)
      --file-process-job-workers int       number of goroutine workers that process files collecting stats (default 8)
      --file-summary-job-queue-size int    the size of the queue used to hold processed file statistics before formatting (default 8)
  -f, --format string                      set output format [tabular, wide, json, json2, csv, csv-stream, cloc-yaml, html, html-table, sql, sql-insert, openmetrics] (default "tabular")
      --format-multi string                have multiple format output overriding --format [e.g. tabular:stdout,csv:file.csv,json:file.json]
      --gen                                identify generated files
      --generated-markers strings          string markers in head of generated files (default [do not edit,<auto-generated />])
  -h, --help                               help for scc
  -i, --include-ext strings                limit to file extensions [comma separated list: e.g. go,java,js]
      --include-symlinks                   if set will count symlink files
  -l, --languages                          print supported languages and extensions
      --large-byte-count int               number of bytes a file can contain before being removed from output (default 1000000)
      --large-line-count int               number of lines a file can contain before being removed from output (default 40000)
      --min                                identify minified files
  -z, --min-gen                            identify minified or generated files
      --min-gen-line-length int            number of bytes per average line for file to be considered minified or generated (default 255)
      --no-cocomo                          remove COCOMO calculation output
  -c, --no-complexity                      skip calculation of code complexity
  -d, --no-duplicates                      remove duplicate files from stats and output
      --no-gen                             ignore generated files in output (implies --gen)
      --no-gitignore                       disables .gitignore file logic
      --no-gitmodule                       disables .gitmodules file logic
      --no-hborder                         remove horizontal borders between sections
      --no-ignore                          disables .ignore file logic
      --no-large                           ignore files over certain byte and line size set by large-line-count and large-byte-count
      --no-min                             ignore minified files in output (implies --min)
      --no-min-gen                         ignore minified or generated files in output (implies --min-gen)
      --no-scc-ignore                      disables .sccignore file logic
      --no-size                            remove size calculation output
  -M, --not-match stringArray              ignore files and directories matching regular expression
  -o, --output string                      output filename (default stdout)
      --overhead float                     set the overhead multiplier for corporate overhead (facilities, equipment, accounting, etc.) (default 2.4)
  -p, --percent                            include percentage values in output
      --remap-all string                   inspect every file and remap by checking for a string and remapping the language [e.g. "-*- C++ -*-":"C Header"]
      --remap-unknown string               inspect files of unknown type and remap by checking for a string and remapping the language [e.g. "-*- C++ -*-":"C Header"]
      --size-unit string                   set size unit [si, binary, mixed, xkcd-kb, xkcd-kelly, xkcd-imaginary, xkcd-intel, xkcd-drive, xkcd-bakers] (default "si")
      --sloccount-format                   print a more SLOCCount like COCOMO calculation
  -s, --sort string                        column to sort by [files, name, lines, blanks, code, comments, complexity] (default "files")
      --sql-project string                 use supplied name as the project identifier for the current run. Only valid with the --format sql or sql-insert option
  -t, --trace                              enable trace output (not recommended when processing multiple files)
  -u, --uloc                               calculate the number of unique lines of code (ULOC) for the project
  -v, --verbose                            verbose output
      --version                            version for scc
  -w, --wide                               wider output with additional statistics (implies --complexity)
```

Output should look something like the below for the redis project

```text
$ scc redis 
───────────────────────────────────────────────────────────────────────────────
Language                 Files     Lines   Blanks  Comments     Code Complexity
───────────────────────────────────────────────────────────────────────────────
C                          437   267,353   31,103    45,998  190,252     48,269
JSON                       406    25,392        4         0   25,388          0
C Header                   288    48,831    5,648    11,302   31,881      3,097
TCL                        215    66,943    7,330     4,651   54,962      3,816
Shell                       75     1,626      239       343    1,044        185
Python                      34     4,802      694       498    3,610        621
Markdown                    26     4,647    1,226         0    3,421          0
Autoconf                    22    11,732    1,124     1,420    9,188      1,016
Lua                         20       525       69        71      385         89
Makefile                    20     1,956      368       170    1,418         85
YAML                        20     2,696      147        53    2,496          0
MSBuild                     11     1,995        2         0    1,993        160
Plain Text                  10     1,773      313         0    1,460          0
Ruby                         9       817       73       105      639        123
C++                          8       546       85        43      418         43
HTML                         5     9,658    2,928        12    6,718          0
License                      3        90       17         0       73          0
CMake                        2       298       49         5      244         12
CSS                          2       107       16         0       91          0
Systemd                      2        80        6         0       74          0
BASH                         1       143       16         5      122         38
Batch                        1        28        2         0       26          3
C++ Header                   1         9        1         3        5          0
Extensible Styleshe…         1        10        0         0       10          0
JavaScript                   1        31        1         0       30          5
Module-Definition            1    11,375    2,116         0    9,259        167
SVG                          1         1        0         0        1          0
Smarty Template              1        44        1         0       43          5
m4                           1       951      218        64      669          0
───────────────────────────────────────────────────────────────────────────────
Total                    1,624   464,459   53,796    64,743  345,920     57,734
───────────────────────────────────────────────────────────────────────────────
Estimated Cost to Develop (organic) $12,517,562
Estimated Schedule Effort (organic) 35.93 months
Estimated People Required (organic) 30.95
───────────────────────────────────────────────────────────────────────────────
Processed 16601962 bytes, 16.602 megabytes (SI)
───────────────────────────────────────────────────────────────────────────────
```

## Example output

Running against Redis will print a summary like this (values vary by branch and date):

```text
[Stage 0] Extracting git metadata...
[Stage 1] Scanning repository structure and signals...
[Layer 1] Fetching total and authored LOC via SCC...
[Stage 2] Running deep analysis (Tokens & Duplication)...
[Stage 5] Scanning for secrets...

============================================
  Analysis Complete — v3.0.0 (Production Refactor)
============================================
  Authored LOC     : 250,000
  Non-Authored LOC : 4,000
  LLM Tokens (Repo): 1,600,000
  Commits          : 10,000
  Contributors (U) : 500
  Languages        : C, Tcl, Shell
  Rating           : 8.7 / 10  (Excellent)
  Duplication      : 1.2% (token-weighted)
  Secrets found    : 0
  Open Source      : True
  Git History OK   : True

  Report saved to  :
  outputs/redis_analysis.json
============================================
```

Reports are saved as JSON. Project runs also create portfolio decision/summary files and `combined_legacy.csv` in the output directory. See [csv_schema.md](csv_schema.md) for CSV field definitions.

## Notes

- `full` is the default mode and includes deep analysis plus secret scanning.
- Do not commit `.env` or access tokens.
- Use `--policy acceptance-policy.example.yaml` to override project acceptance thresholds.

## License

See [LICENSE](LICENSE).
