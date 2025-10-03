# Scripting

Baygon ships as a CLI, but its parser is intentionally reusable from Python.
Two helper modules are exposed:

* `baygon.loader` – parse YAML/JSON files with friendly error messages.
* `baygon.schema` – validate and normalize the resulting dictionary.

```python
from pathlib import Path
from baygon.loader import load_file
from baygon.schema import normalize_spec

raw = load_file(Path("tests.yml"))
spec = normalize_spec(raw)

for suite in spec.tests:
    print(suite.name, suite.args)
```

`normalize_spec` returns a Pydantic model.  All collections are normalized: for
instance `args` is guaranteed to be a list of strings, stream operations are
already parsed into filter/check objects, and files are represented by
`FileSpec` instances.

## Validating ad-hoc documents

If you receive a configuration from an untrusted source you can still use the
same API:

```python
from pydantic import ValidationError
from baygon.schema import normalize_spec

def validate_config(data: dict) -> bool:
    try:
        normalize_spec(data)
    except ValidationError:
        return False
    return True
```

The resulting models are regular Pydantic objects, so you can convert them back
to dictionaries with `.model_dump()` if you need to serialise the canonical
form.
