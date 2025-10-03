# Config File Syntax

## Schema version

The schema version is the first key of the configuration file. It is mandatory the version is the baygon version. Syntax API might be incompatible between major versions. The following is a minimal example composed of 1 test which tests if the output is 3 when the binary is run with two arguments `1` and `2`:

```yaml
version: 1.0 # Can use semantic versioning
tests:
  - args: [1, 2]
    stdout: 3
```

## Filters

Filters can be applied to all outputs (`stdout`, `stderr`) of every tests. The following filters are available:

`uppercase`

:   All outputs are transformed into uppercase.

    ```yaml
    filters:
      - uppercase: true
    ```

`lowercase`

:   All outputs are transformed into lowercase.

    ```yaml
    filters:
      - lowercase: true
    ```

`trim`

:   All outputs are trimmed (spaces are removed from both ends), on each line

    ```yaml
    filters:
      - trim: true
    ```

`chomp`

:   Trailings newlines are removed from all outputs.

    ```yaml
    filters:
      - chomp: true
    ```

`stripall`

:   All spaces are removed from all outputs.

    ```yaml
    filters:
      - stripall: true
    ```

`regex`

:   A remplacement is made using regular expressions. Multiple forms are accepted. Either a PCRE expression or a search and replace form.

    ```yaml
    filters:
      # PCRE expression
      - regex: 's/foo(bar)?/bar/g'
      # Search and replace form
      - regex:
        search: foo(bar)?
        replace: bar
      # Search and replace in an array
      - regex: [foo(bar)?, bar]
    ```

`replace`

:   A remplacement is made using a string.

    ```yaml
    filters:
      - replace:
        search: foo
        replace: bar
      - replace: [foo, bar]
    ```

Multiple filters can be applied at the same time:

```yaml
version: 1
filters:
  - lowercase: true
  - regex: [foo(bar)?, bar]
tests:
  - args: [1, 2]
    stdout: 3
```

Filters can also be applied at any level (root, group, test), they override the previous definitions:

```yaml
version: 1
tests:
  - args: [1, 2]
    stdout:
      - contains: foo
      - regex: f(oo|aa|uu)
    filters:
      - lowercase: true
```

Or even at a stream output level:

```yaml
stdout: [{ filters: [ trim: true ], equals: 3 }]
```

## Naming

Tests and groups can be optionally named:

```yaml
version: 1
tests:
  - name: Test functionality of the additionner
    args: [--add, 40, 2]
    stdout: 42
  - name: Test error if less than two arguments
    args: []
    exit: 2
```

## Groups and subgroups

Tests can be grouped into hierarchical sub sections, by nesting each test into categories:

```yaml
version: 1
tests:
  - name: Category 1
    tests:
      - args: [1, 2]
        stdout: 3
  - name: Category 2
    tests:
      - name: Subcategory 1
        tests:
          - args: [1, 2]
            stdout: 3
```

## Exit status

The exit status can be checked with the `exit` key followed with a 8-bit integer. The following checks if the program returns 0

```yaml
version: 1
tests:
  - exit: 154
  - exit: 0x9a
  - exit: Oo232
  - exit: -102
```

The value can be expressed in unsigned, signed or hexadecimal form. Baygon automatically interprets the value in unsigned form (0 to 255).

You may want to test ranges of exit status:

```yaml
version: 1
tests:
  - exit:
      - gt: 0  # Greater than 0
      - '>': 0

      - lt: 255 # Less than 255
      - '<': 255

      - gte: 0 # Greater or equal to 0
      - '>=': 0

      - lte: 255 # Less or equal to 255
      - '<=': 255
```

In POSIX some exit status are used for specific purposes.

| Signal  | Signification            | Exit Status |
| ------- | ------------------------ | ----------- |
| SIGHUP  | Hangup                   | 129         |
| SIGINT  | Interrupt                | 130         |
| SIGQUIT | Quit                     | 131         |
| SIGILL  | Illegal instruction      | 132         |
| SIGABRT | Aborted                  | 134         |
| SIGFPE  | Floating point exception | 136         |
| SIGKILL | Killed                   | 137         |
| SIGSEGV | Segmentation fault       | 139         |
| SIGTERM | Terminated               | 143         |

## Checking outputs

Both `stdout` and `stderr` can be tested against multiple conditions:

```yaml
tests:
  - stdout:
      - contains: foo # Must contain the word foo
      - regex: f(oo|aa|uu) # Must match
    stderr:
      - equals: foobar # Must be exactly equal to foobar
```

The available conditions are:

`contains`

:   The output must contain the string.

    ```yaml
    stdout:
      - contains: foo
    ```

`regex`

:   The output must match the regular expression.

    ```yaml
    stdout:
      - regex: f(oo|aa|uu)
    ```

`equals`

:   The output must be strictly equal to the string.

    ```yaml
    stdout:
      - equals: foobar
    ```

`negate`

:   This is a special condition that negates the following condition. It is useful when you want to negate a condition that is not available. For example, you want to test if the output does not contain a string:

    ```yaml
    stdout:
      - negate:
        - contains: foo
    ```

## Executable

Baygon allows for specifying the executable to run either from the command line or from the configuration file. You may specify an executable at any level (root, group, test). The only condition is that an executable must be specified before any test.

```yaml
tests:
  - name: Test ./foo
    executable: ./foo
    stdout: I am Foo
  - name: Test ./bar
    executable: ./bar
    stderr: I am bar
  - name: Group
    executable: ./baz
    tests:
      - name: Test 1
        exit: 0
```

The executable is therefore propagated through the test tree, but you cannot override it. Thus, the following is invalid:

```yaml
tests:
  - executable: ./foo
    tests:
      - executable: ./bar
```

One common approach is to name the executable at the top level:

```yaml
version: 1
executable: ./foobar
tests:
  - name: Test ./foobar
    exit: 0
```

Or even from the shell:

```console
baygon ./foobar
```

!!! note

    The current working directory `cwd` is the directory of the config file, except if you specify the executable from the shell. In this case the working directory is the current directory.

### Environment variables

You can specify environment variables for the executable at any level:

```yaml
env: [FOO=bar, BAR=foo]
```

### TTY

Some programs behave differently when they are run in a TTY. You can specify the `tty` key to run the program in a TTY. By default, the program is run in a non-TTY environment.

```yaml
tty: true
```

### Timeout

You can specify a timeout for the executable. The timeout is in seconds.

```yaml
timeout: 5
```

### Arguments

You can specify arguments for the executable. The arguments are passed as an array.

```yaml
args: [1, 2]
```

### Input

You can specify an input for the executable. The input is either a string or a file.

```yaml
input: 'foo bar'
```

```yaml
input:
  file: input.txt
```

The working directory is the directory of the configuration file or the one specified with `cwd`.

## Configuration file

When running `Baygon` without specifying a configuration file, it will look for a file named `baygon.yml` recursively in the current directory and its parents. If no file is found an error is raised.

You can specify a different file with the `-c` or `--config` option:

```console
baygon --config other.yaml
```

You are flexible in the format of the configuration file. The following formats are supported:

```text
baygon.yml
baygon.yaml
baygon.json
```

!!! note

    The names `t.json`, `tests.json` are now deprecated, use `baygon.json` instead.

## Loops and expressions

If the `eval` mode is enabled, you can use loops and expressions in the configuration file. The following is an example of a loop that runs the program with arguments from 1 to 10:

```yaml
version: 1
eval: true
tests:
  - args: ['{{i = iter(1, 10)}}']
    stdout: '{{i}}'
```

The test will be executed 10 times, from 1 to 10 and the output is checked against the value of `i`.

The `eval` option will search for mustaches `{{` and `}}` and evaluate the expression inside. You can use standard arithmetic operators and functions. The following iterators are available:

`iter(start, end, step=1)`

:   Starts a new iterator for this test and returns the current value. The iterator is incremented by `step` at each iteration.

    ```yaml
    args: ['{{i = iter(1, 10)}}'] # For integers
    args: ['{{i = iter(1.0, 10.0, 0.5)}}'] # For floats
    args: ['{{i = iter("a", "z")}}'] # For characters
    args: ['{{i = iter([4, 8, 15, 16, 23, 42])}}'] # For arrays
    ```

`rand(min, max, iterations=1, seed=0)`

:   Returns a random number between `min` and `max`.

    ```yaml
    args: ['{{i = rand(1, 10, 10)}}'] # 10 random numbers between 1 and 10
    ```

You can use complex expressions such as:

```yaml
args: ['{{a = iter(-10, 10)}}', '{{b = iter(-10, 10)}}']
filters:
  - chomp: true
stdout: '{{a}} + {{b}} = {{a + b}}'
```

The math functions available are:

```text
sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, asinh, acosh, atanh, sqrt, exp, log, log10, log2, pow, ceil, floor, round, abs, min, max, std, median, sum
```

Behind the scenes, Baygon uses an isolated environment to evaluate the expressions. You may want to add your own functions instead of `eval`:

```yaml
eval:
 - from statistics import mean
 - from math import sqrt
```

### Custom initialization

You can specify custom initialization code that is run before the tests. The code is run in the same environment as the expressions.

```yaml
eval:
  start: '{{'
  end: '}}'
  init: |
    def foo(x):
        return x + 1
```

The code is run before each tests.

You can redefine the start and end delimiters if you want to.
