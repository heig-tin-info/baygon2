# Academic Assignment

Baygon is well designed to handle academic assignments. You can specify the points for each test, group of tests or at the top level.

The configuration keys you can use are:

**`points`**

: The total points that can be earned from the whole suite, group of tests or test.

**`weight`**

: The weight of a test or group of tests. The weight is used to calculate the available points. A default `weight` value of `10` is used but you can set it to any value you want according to your needs.

**`min-points`**

: When using weights, for instance if you have a group of test awarded 2 points shared in three tests of equally weights, each test will be awarded 0.666...points. The `min-points` key allows you to set a minimum value for the points. In this case, if you set `min-points` to `1`, each test will be awarded 1 point. Typical values are `1`, `0.5`, `0.25` or `0.1`.

Baygon will automatically figure out how to assign points to each test based on your entries. Some rules apply:

1. Without any other information each successfull test is awarded 1 points.
2. If a total number of points is specified at any level, the points are distributed equally among the subtests.
3. Weights can be used influence the distribution of points. The default weight is 10.

To give you some examples we will simplify the configuration files.

## Equally distributed points

By default we know that `min-points` is 0.1 and with equal `weight` on each test, the points are distributed equally.

```yaml
version: 1
points: 10
tests:
  - name: Test 1 # 3.4
  - name: Test 2 # 3.3
  - name: Test 3 # 3.3
```

## Weighted points distribution

This time we have two subgroups of tests. The first group has a weight of 5 and the second group has a weight of 10. The total points are 10.

```yaml
version: 1
points: 12
tests:
  - name: Group 1 # 4
    weight: 5
    tests:
      - name: Test 1 # 2
      - name: Test 2 # 2
  - name: Group 2 # 8
    weight: 10
    tests:
      - name: Test 3 # 4
      - name: Test 4 # 4
```

## Using the result

The number of points is given on the output it has the form of:

```text
Points: 4/10
```

Alternatively you may want to use the report feature to generate a report in JSON or YAML format. The report will contain the points for each test and group of tests.

```console
baygon --report=report.json
```

This report could be used by a grading system to automatically assign grades to students.
