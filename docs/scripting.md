# Scripting

Baygon is meant to be used as a standalone program to test other programs using a configuration file. However, you can also use Baygon as a library to write your own test runner.

Here is an example of a test runner using Baygon:

```python
from pathlib import Path
import baygon

ts = baygon.TestSuite({
        'filters': {'uppercase': True},
        'tests': [{
            'args': ['--version'],
            'stderr': [{'contains': 'VERSION'}]
        }]
    }, executable=Path('myapp'))
t = ts.run()

assert(t, [[]])
```

## Validation

You can validate a Baygon configuration file with the `baygon.Schema` function:

```python
import baygon

data = baygon.Schema({
    'version': 1,
    'tests': [{
        'name': 'Test',
        'exit': 0
    }]
})

assert(data['version'], 1)
```
