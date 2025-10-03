# Structure

```text
baygon/
├─ src/baygon/
│  ├─ __init__.py
│  ├─ cli.py                 # Entrée CLI (Typer/Click)
│  ├─ schema.py              # Modèles Pydantic (syntaxes compacte & canonique)
│  ├─ loader.py              # Chargement YAML/JSON, normalisation, erreurs lisibles
│  ├─ merge.py               # Héritage/merge (add-only, jamais de suppression)
│  ├─ plan.py                # Expansion matrix/repeat → cas concrets (TestPlan)
│  ├─ context.py             # Contexte d’exécution (variables, x++/++x, RNG seed)
│  ├─ exec.py                # Lancement subprocess (asyncio), timeouts, ulimit
│  ├─ pipeline.py            # Application des filters → checks sur stdout/stderr/files
│  ├─ filters/
│  │  ├─ __init__.py
│  │  ├─ builtin.py          # trim, lower, upper, sub (PCRE), map_eval, …
│  ├─ checks/
│  │  ├─ __init__.py
│  │  ├─ builtin.py          # match (PCRE), contains, equals, lt/gte, check_eval, capture
│  ├─ reporters/
│  │  ├─ __init__.py
│  │  ├─ rich_reporter.py    # sortie console pédagogique (Rich)
│  │  ├─ junitxml.py         # export JUnit XML (CI)
│  │  ├─ gh_annotations.py   # annotations GitHub Actions
│  ├─ plugins.py             # Découverte des plugins (entry points) + résolution nom
│  ├─ errors.py              # Exceptions métiers bien expliquées
│  ├─ compat.py              # Windows/POSIX, encodages, shell runner
│  └─ utils.py
├─ tests/                    # Tests unitaires/e2e de baygon (pytest)
├─ examples/                 # Jeux de tests commentés
├─ pyproject.toml
├─ README.md
└─ mkdocs.yml                # (si mkdocs)
```
