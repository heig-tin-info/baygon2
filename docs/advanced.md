# Advanced

## Test on source files

You may want to execute tests on source files. This is possible by using `cat` as executable:

```yaml
version: 1
tests:
  - name: Test function foo
    executable: cat
    stdin: foo.c
    stdout:
      - regex: void\s+foo\s*\(\s*int\s+\w+\)
```

