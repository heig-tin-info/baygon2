Je suis en train de réaliser un unit tester moderne en Python pour tester de manière arbitraire des exécutables ou des scripts. Bien que pytest exist et que d'autres existent pour le C/C++... tous ces framework sont orientés développeur avec des sorties toujours assez criptiques et pas très lisibles des étudiants. L'objectif est d'avoir une syntaxe claire pour les tests et une sortie très lisible mise en forme avec rich par exemple. Les tests sont décrits dans un fichier yaml ou json. L'utilitaire s'appelle baygon.

Voici un premier jet de la syntaxe d'un tests. Je t'ai mis aussi une documentation sur la syntaxe.

Quelques points importants.

La plupart des clés (filters, setup, teardown, ...) sont héritées, c'est à dire que dans les sous clés chaque test hérite des éléments déjà configurés. Ce qui permet de satisfaire à SSOT et DRY.

version: 1
exec:
  cmd: ./a.out # Command to execute (string or list of strings)
  timeout: 5 # Optional timeout in seconds (default: no timeout)
  stdin: null # Optional stdin input (string or list of strings, default: None)
  args: [] # Optional list of arguments to the command (default: [])
  env: {} # Optional environment variables to set (default: inherit from parent)
  cwd: null # Optional working directory to run the command in (default: current directory)
  shell: false # Optional flag to run the command in a shell (default: false)
filters: # Optional root key for filters applied to all outputs (stdout, stderr, files)
  - trim: {} # Strip whitespace from start and end of all outputs
tests: # Mandatory root key
  - name: Arguments check # Name of the test suite (group of tests)
    tests: # Mandatory key for grouping tests
      - name: No errors if two arguments # Name of the individual test
        description: "Checks that the program runs without errors when provided with two arguments." # Optional description of the test
        stdin: "Input data for stdin (string or list of strings)" # Optional stdin input (string or list of strings)
        args: [1, 2] # Input arguments to the program (coerce int/flotat/bool to str)
        exit: 0 # Expected exit code (if omitted, defaults to None, no check)
      - name: Error if less than two arguments # A second individual test
        args: [1]
        exit: 1
  - name: Stdout is the sum of arguments
    args: [1, 2]
    filters: {} # Override root filters (empty list means not over
    stdout: # Check of stdout (if omitted, no check), checks are run in order
      - regex: '\b\d\.\d\.\d\b' # Use PCRE regex to check stdout
      - filter: 's/\s+//g' # Apply this filter to stdout before checks (can be repeated), by default it is regex filter
      - contains:
          value: "Version" # Check that stdout contains this string
          explanation: "La sortie doit contenir le mot Version, votre sortie est {}" # Optional explanation if the test fails, explaination can be used for each test case with the value/explaination keys si donné sous forme de dict
      - not_contains: "Error" # Check that stdout does not contain this string
      - equals: "3" # Check that stdout is exactly this string
      - eval: "int(value) * 2 == 6" # Check that the captured group passes this python expression (value is the captured string)
      - capture:
        regex: '(\d+)' # Capture a regex group from stdout
        tests:
          - equals: "3" # Check that the captured group is exactly this string
          - not_equals: "4" # Check that the captured group is not exactly this string
          - regex: '\d' # Check that the captured group matches this regex
          - lt: 4 # Check that the captured group is less than this value (coerced to int/float)
          - python: "int(value) * 2 == 6" # Check that the captured group passes this python expression (value is the captured string)
      - filter:
        - regex: 's/\s+//g' # Apply this filter to stdout before checks (can be repeated), by default it is regex filter
        - trim: {} # Strip whitespace from start and end of stdout
        - lower: {} # Convert stdout to lowercase
        - upper: {} # Convert stdout to uppercase
    stderr: [] # No tests on stderr...
    files:
      foo.yml: # Check output on generated file foo.yml
  - name: Version on stderr # Another test suite
    args: ["--version"]
    stderr:
      - regex: '\b\d\.\d\.\d\b'
      - contains: "Version"
  - name: Test with eval # Another test suite
    args: [1, 2]
    tests:
      - name: Loop
        repeat: 10 # Repeat this test 10 times in the same context
        setup: # Setup commands to run before this test
          - run: something called before
          - eval: | # Init some variables in eval mode
              import random
              x = random.randint(1, 100)
              y = random.randint(1, 100)
        teardown: # Teardown commands to run after this test
          - run: something called after
        stdin: "({{ x++ }} + {{ y }}) * 42", # x is incremented on each iteration, what is printed is the result of (x + y) * 42, syntax ()++ and ++() is supported, the pre and post incr is done before or after the test.
        args:
          - "-e"
          - "print eval <STDIN>"
        stdout:
          equals: "{{ (x + y) * 42 }}"

...
# Documentation of the syntax
---
syntax:
  filters:
    trim: "Strip whitespace, new lines from start and end of all outputs"
    lower: "Convert all outputs to lowercase"
    upper: "Convert all outputs to uppercase"
    regex: "Apply a regex substitution to all outputs, takes a PCRE regex as argument"
    eval: "Apply a python expression to all outputs, takes a python expression as argument, the output is in the variable 'value'"
  tests:
    name: "Name of the test suite (group of tests)"
    description: "Optional description of the test suite"
    tests: "Sub-key for grouping tests"
    repeat: "Optional number of times to repeat this test in the same context default is 1"
    setup: "Optional list of commands to run before this test"
    teardown: "Optional list of commands to run after this test"
    stdin: "Optional stdin input (string or list of strings)"
    args: "Input arguments to the program (coerce int/flotat/bool to str)"
    exit: "Expected exit code (if omitted, defaults to None, no check)"
  streams:
    stdout: "Check of stdout"
    stderr: "Check of stderr"
    files: "Check output on generated files"
  checks:
    regex: "Use PCRE regex to check the stream"
    contains: "Check that the stream contains this string"
    not_contains: "Check that the stream does not contain this string"
    equals: "Check that the stream is exactly this string"
    not_equals: "Check that the stream is not exactly this string"
    lt: "Check that the stream is less than this value (coerced to int/float)"
    lte: "Check that the stream is less than or equal to this value (coerced to int/float)"
    gt: "Check that the stream is greater than this value (coerced to int/float)"
    gte: "Check that the stream is greater than or equal to this value (coerced to int/float)"
    eval: "Check that the stream passes this python expression (value is the stream)"
    capture: "Capture a regex group from the stream and run sub-tests on it"
    filter: "Apply a filter to the stream before checks (can be repeated), by default it is regex filter"


Peux-tu me faire :

1. Un retour sur l'idée du projet, la pertinence par rapport à d'autres projets déjà existants
2. Un retour sur la cohérence de la syntaxe et des suggestions d'amélioration
3. Des idées futures ou des choses que j'aurais manquées
---

Super idée 👏 : un runner de tests “agnostique langage” pensé pour les étudiants, avec une syntaxe lisible et des rendus Rich. Tu touches un vrai besoin que ni `pytest` (trop “dev”), ni `bats`/`expect` (trop shell/cryptiques), ni `Robot Framework` (lourd, orienté mots-clés) ne couvrent vraiment pour le “je lance un exécutable / un script et j’explique clairement ce qui se passe”.

Voici mon retour en 3 volets.

# 1) Pertinence & positionnement

* **Baygon vs pytest**
  `pytest` sait très bien tester des CLIs (capturer stdout/stderr, rc) mais la *spécification* des cas est du Python, et le rendu par défaut reste verbeux pour des débutants. Tu apportes : a) une *DSL déclarative* (YAML/JSON), b) une *sortie pédagogique* (Rich), c) des *pipes de filtres* pour “nettoyer” les sorties avant assertions.
* **Baygon vs bats / shUnit / cram**

  * `bats` & co ⇒ proches du shell, peu attirants pour les étudiants non-shell.
  * `cram` ⇒ très minimaliste “golden diff”, peu de logique/paramétrage, pas d’héritage ni de filtres riches.
    Baygon peut englober ces usages avec plus d’ergonomie et d’explicabilité.
* **Baygon vs Robot Framework**
  Robot est puissant, mais verbeux, orienté “keywords” et bibliothèques. Ton approche est *plus simple* pour “tester un binaire avec stdin/args/env et vérifier la sortie avec quelques transformations”.
* **Baygon vs LLVM lit / FileCheck**
  `lit` / `FileCheck` sont excellents pour toolchains, mais l’entrée est plus technique et le rendu n’est pas pensé “pédagogie”. Baygon peut emprunter des idées (vérifs de fragments, normalisations), avec un UX moderne.
* **Valeur ajoutée clé**

  * **Lisibilité & feedback pédagogique** (messages d’échec compréhensibles, couleurs, diff propre).
  * **DRY/SSOT via héritage**.
  * **Pipelines de filtres** (normaliser timestamps, chemins, locales…).
  * **Portabilité** (n’importe quel exécutable/script).

# 2) Cohérence de la syntaxe & améliorations

Globalement la grammaire est claire. Quelques points à durcir pour éviter l’ambiguïté et faciliter l’implémentation :

## a) Schéma & cohérence des structures

* **Toujours des listes ordonnées** pour `filters` et pour chaque `stdout`/`stderr`/`files.<name>` : chaque étape = `{<op>: <args>}` (une seule clé par objet).
  Évite d’alterner entre scalaires et objets : p.ex. `- contains: "Version"` **ou** `- contains: { value: "Version", explanation: "…"} `, mais pas les deux formes dans le même fichier.
* **Séparer match vs transform**
  Tu utilises `regex` tantôt pour *matcher*, tantôt `filter: 's/…/…/g'` pour *substituer*. Je proposerais :

  * `- match: { regex: "…" , flags: "mi" }` (assert)
  * `- sub:   { regex: "…", repl: "…", flags: "gmi" }` (transform)
    Ainsi, pas de confusion.
* **Nom de l’op “eval”**
  Tu as `eval` à deux endroits (assertion et filtre). Pour lever l’ambiguïté :

  * `check_eval:` pour l’assertion (retourne bool)
  * `map_eval:` pour le filtre (retourne nouvelle valeur)
* **PCRE vs Python `re`**
  Tu écris “PCRE”. Le moteur `re` de Python **n’est pas** PCRE. Deux options :

  1. Déclarer officiellement “moteur = Python `re`” + doc sur flags, ou
  2. Utiliser le module `regex` (compatible PCRE-like) et le documenter.
     Dans tous les cas, expose `flags` (`i`, `m`, `s`, `x`).
* **Types & coercions**

  * `args: [1, 2]` ⇒ préciser que tout est stringifié via `str()`.
  * Comparaisons `lt/lte/gt/gte` ⇒ préciser coercion à `int`/`float` et règles d’erreur si non numérique.
  * `stdin` (string **ou** list) ⇒ si list, jointure avec `\n` (ou `\0` si option).
* **Héritage & surcharge**
  Documenter précisément la **stratégie de merge** :

  * Dictionnaires : *deep-merge* (clé à clé).
  * Listes (`filters`) : **concat** par défaut, avec moyens explicites pour *remplacer* (`filters: []`) ou *préfixer* (`prepend_filters:`).
  * Champs scalaires : *override* simple.
    Écrire une petite table “root → suite → test” avec exemples.
* **`repeat` & templating**
  Ta notation `{{ x++ }}` n’est ni Jinja ni Python. Décide :

  * soit **Jinja2** (`{{ x }}`) + filtres, et fournis des *functions* `inc('x')`/`range()` pour itératifs,
  * soit un **mini langage** (type `expr`) avec `pre`/`post` incr clairs.
    Mon conseil : **Jinja2 + contexte contrôlé** (et un `loop.index` comme en Jinja).
* **`capture`**
  Très bonne idée. Je formaliserais :

  ```yaml
  - capture:
      regex: "(\\d+)"
      group: 1           # défaut 1
      as: "sum"          # optionnel, met dans le contexte
      tests:
        - equals: "3"
        - lt: 4
  ```

  Et permettre de réutiliser `{{ sum }}` dans la suite du flux (stdout/stderr/files).
* **`files`**
  Définir la structure :

  ```yaml
  files:
    foo.yml:
      filters: [ … ]
      checks:
        - exists: true
        - yaml_valid: true
        - jsonpath: { path: "$.a.b", equals: "42" }
  ```

  (cf. section “extensions” ci-dessous).
* **Ergonomie des messages d’échec**
  Tu as `explanation`. Super. Normalise la signature : `explain:` partout (ou `message:`). Autoriser des *templates* :
  `explain: "La sortie doit contenir {{ value|repr }}, obtenu {{ got|repr }}"`.

## b) Petites incohérences / coquilles dans l’exemple

* `filters: {} # Override root filters (empty list means not over` → commentaire tronqué, et `{}` n’est pas une liste. Mets `filters: []` pour “aucun filtre”.
* `stdin: "({{ x++ }} + {{ y }}) * 42",` → virgule finale invalide en YAML.
* `python:` vs `eval:` pour les checks : choisis un seul nom (cf. plus haut).
* `regex: '\b\d\.\d\.\d\b'` : en YAML, `\b` peut être interprété ; préfère `"\\b\\d\\.\\d\\.\\d\\b"` ou triple quotes.
* `shell: false` mais tu proposes `args: ["-e", "print eval <STDIN>"]` : ce genre d’usage dépend du shell. Soit `shell: true`, soit précises que `cmd` est le binaire *et* `args` ne passent pas par un shell.

## c) Sécurité & déterminisme

* **Évaluation de code** : `eval` est dangereux. Utilise un *évaluateur restreint* (p.ex. `asteval`, `simpleeval`) avec **builtins filtrés**, pas d’`import`, pas d’I/O.
* **RNG** : quand tu utilises `random`, expose `seed` contrôlable au niveau suite/test (`seed: 1234`) pour rejouabilité.
* **Temps & ressources** : `timeout` par *phase* (`setup`, `exec`, `teardown`), limites CPU/mémoire (`ulimit`, cgroups), *kill-tree*.

# 3) Idées futures & manques possibles

### a) Transformations & checks avancés

* **Normalisations prêtes à l’emploi** :
  `normalize_timestamps`, `normalize_uuids`, `normalize_paths`, `normalize_floats: { precision: 6 }`.
* **Checks structurés** :

  * `json_valid`, `yaml_valid`, `toml_valid`
  * `jsonpath`, `jq` (si dispo), `xpath`
  * `schema`: JSON Schema pour valider un fichier/sortie JSON.
* **Diffs lisibles** :

  * `equals_file: expected/xyz.out` avec **unified diff** et mode *ignore-ws*.
  * **Snapshot testing** (`snapshot: true` + `--update-snapshots`).
* **Matrices**
  `matrix: { args: [[1,2],[2,3]], env.FOO: [A,B] }` ⇒ produit N tests paramétrés.
* **Contrôle de flakiness**
  `retry: { attempts: 3, delay_ms: 100 }` + `flaky: true` pour ne pas bloquer un TP à cause d’un test instable.
* **Assertions temporelles & perfs**
  `duration_lt_ms: 50`, `stdout_within_ms: 10_000`.
* **Events hooks**
  `before_all`, `after_all`, `before_each`, `after_each` (avec héritage) en plus de `setup/teardown` par test.
* **Sandbox & isolation**

  * Dossiers temporaires par test (`workdir: tmp` auto).
  * Option Docker/Podman : `container: { image: "python:3.12", mount: ["./:/work"] }` pour reproductibilité multi-OS.
  * Montées de droits interdites.
* **Multi-plateforme**
  Gestion de `shell`/chemins sous Windows (PowerShell) vs Unix (`sh`). Permettre `runner: bash|powershell|cmd`.
* **Rapports & intégrations CI**

  * Sorties : `rich` en console **+** `junitxml`, `TAP`, `Allure` optionnels.
  * Annotations GitHub Actions (`::error file=…,line=…::message`).
  * `--list` (lister), `--grep "Version"`, `--fail-fast`, `--max-workers`.
* **Plugins**
  Architecture simple : *filters*, *checks*, *reporters*, *resolvers* (p.ex. charge un fichier attendu depuis une URL).
* **Schéma & tooling**

  * Publier un **JSON Schema** pour YAML/JSON ⇒ autocomplétion dans IDEs.
  * `baygon lint` pour valider la spec.
  * `baygon explain` : imprime la config **après héritage/merge** (très pédagogique).
* **Internationalisation**
  Messages d’erreur localisables : `locale: fr` / `en`, catalogues de strings Rich.
* **Nom & marque**
  “Baygon” est une marque d’insecticide célèbre. Si tu comptes publier, vérifie les aspects juridiques/trademark ; sinon trouve un nom alternatif (même si le clin d’œil est drôle 😅).

# Proposition de mini-refonte (extrait)

```yaml
version: 1
defaults:
  exec:
    cmd: ./a.out
    timeout: 5
    shell: false
  filters:
    - trim: {}
    - sub: { regex: "\\r\\n", repl: "\n", flags: "g" }

tests:
  - name: Arguments check
    tests:
      - name: Runs with two args
        args: [1, 2]
        stdin: "hello"
        exit: 0
      - name: Fails with one arg
        args: [1]
        exit: 1

  - name: Stdout is sum of arguments
    args: [1, 2]
    stdout:
      - match: { regex: "\\b\\d+\\.\\d+\\.\\d+\\b" }   # version banner
      - sub:   { regex: "\\s+", repl: "", flags: "g" } # normalize spaces
      - contains:
          value: "Version"
          explain: "La sortie doit contenir 'Version', obtenu {{ got|truncate(80) }}"
      - not_contains: "Error"
      - equals: "3"
      - check_eval: "int(value) * 2 == 6"
      - capture:
          regex: "(\\d+)"
          as: "sum"
          tests:
            - equals: "3"
            - not_equals: "4"
            - match: { regex: "\\d" }
            - lt: 4
            - check_eval: "int(value) * 2 == 6"
    files:
      foo.yml:
        checks:
          - exists: true
          - yaml_valid: true

  - name: Version on stderr
    args: ["--version"]
    stderr:
      - match: { regex: "\\b\\d+\\.\\d+\\.\\d+\\b" }
      - contains: { value: "Version" }

  - name: Loop with templating
    matrix:
      y: [10, 20]
    repeat: 10
    setup:
      - map_eval: "ctx['x'] = 0 if 'x' not in ctx else ctx['x']"   # contexte sûr
    tests:
      - name: Iter
        map_eval: "ctx['x'] = ctx['x'] + 1"                        # ++
        stdin: "({{ x }} + {{ y }}) * 42"
        args: ["-e", "print(eval(open(0).read()))"]
        stdout:
          - equals: "{{ (x + y) * 42 }}"
```

# Derniers conseils pratiques d’implémentation

* **Exécuteur** : `asyncio.create_subprocess_exec`, capture séparée stdout/stderr, encodage UTF-8, limites de taille, *kill-group* sur timeout.
* **Pipelines** : chaque flux => `value` (str) + `meta` (captures). Applique `filters` (transform) **puis** `checks` (assert).
* **Rapport Rich** :

  * Timeline par test (setup/exec/teardown avec durées).
  * Diff unifié pour `equals/equals_file`.
  * Panneaux “Contexte” (args/env/cwd), “Entrées” (stdin), “Sorties” (stdout/stderr tronquées).
  * “Why it failed?” = `explain` + snippet surligné.
* **JSON Schema** pour verrouiller la syntaxe dès la v1.
* **Tests de baygon lui-même** : dogfooding (baygon teste baygon).

Si tu veux, je peux te proposer un **JSON Schema v1** et un **exécuteur minimal** (100-150 lignes) pour figer les conventions ci-dessus.

---

Je trouve que les deux formes dans le fichier c'est bien

- contains: "value"

ou

- contains:
    value: "value"
    explaination: "explain"

Ca permet de simplifier la syntaxe, tout en restant minimaliste en ayant par défaut la valeur si personne ne veut s'encombrer d'une explication. Il faudra laisser à pydantic le soin de supporter les deux entrées et de les convertir en une forme canonique value/explaination. Il faut distinguer la syntaxe de saisie très permissive et compacte et la syntaxe canonique très verbeuse et complète.

Oui toujours des lists ordonnées pour filters et pour chaque stdout/stderr...

D'accord pour match et sub c'est bien, même si je suis attaché à la syntaxe perl très complete avec m!!i ou s@@gmi plutôt que d'avoir différentes clés. C'est triste que cette syntaxe ne soit pas retenue en Python par défaut mais PCRE est accessible en Python je crois.

Ok pour le nom eval: check_eval et filter_eval

Par défaut je préfère largement PCRE le moteur de Python est à chier pour les re. Du reste tous les nouveaux projets bash/cli utilisent PCRE plus volontiers puisqu'ils sont écrits en Rust.

OK pour stdin avec list avec jointure \n ou \0 en option supplémentaire.

Stratégie de merge la plus simple: on override toujours en ajoutant, on ne supprime pas, ce qui respecte Liskov. Un sous test ne peut pas supprimer un filtre global par exemple. Donc filters: [] ne fait donc rien, il conserve les tests d'avant.

J'aime la syntaxe x++ et ++x elle peut être pré parsée et remplacée par une syntaxe Jinja derrière mais j'éviterai du jinja on capture juste les {{ }} avec un parseur simple  et on évalue simplement. Par sur que jinja soit adapté il est trop complexe ici on veut rester volontairement simple.

Pour capture c'est trop compliqué on a pas besoin du nom du group ca doit rester simple.

Oui pour files oublie les yaml_valid, jsonpath c'est pas des filtres qui doivent être ajoutés par défaut. le exists ne sert à rien si le nom d'un fichier est mentionné c'est que le fichier doit exister donc la clé est inutile.

La clé explain me semble très bien. D'accord trop compliqué le |repr pas à la portée d'un étudiant de comprendre la syntaxe.

Un évaluatieur comme asteval ou simpleval me semble bien. Effectivement un timeout et ulimit me semble nécessaire comme clé qui peut être globale ou individuelle par test.

Pour les idées futures on peut imaginer des plugins sous forme de modules supplémentaires installable qui offrent des filtres ou des checks supplémentaire à ajouter à la syntaxe. par exemple

pip install baygon baygon-normalize-uuids

Dans le cas ou une erreur de syntaxe yml par exemple normalize_uuids est utilisé comme filtre mais qu'il n'est pas installé une erreur de type:

Unknown filter 'normalize_uuids' is it a third-party filter your forgot to install: suggest to pip install baygon-normalize_uuids if exists.  Plutôt que de kill le parse avec une erreur critptique : invalid syntax.

J'aime l'idée de matrix !

L'idée de sandobox ou container est séduisante mais on va la conserver pour plus tard.

Annotation Github a prévoir c'est bien !

les commandes baygon lint et baygon explain c'est très bien.

Localisation utile mais dans une configuration globale .baygonrc par exemple chaque utilisateur peut avoir sa locale mais pas indispensable.

Peux-tu vérifier les aspects juridiques/trademark si je peux avoir un projet opensource de ce nom ?

Avec tout ceci. Peux-tu me suggérer :

1. L'architecture générale du projet (fichiers, étapes de traitement...)
2. Technologies (pydantic?, click?))
3. Technologie pour la documentation du projet ? (vue press, mkdocs-material...?)

---

Top, on a une vision claire. Voici un plan concret et pragmatique pour faire naître “baygon” (et un mot sur le nom à la fin).

# 1) Architecture générale

```
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

## Cycle d’exécution (pipeline)

1. **load** → charge le YAML/JSON, supporte *forme compacte* **ou** *canonique*, normalise via `schema.py` (Pydantic).
2. **validate** → messages d’erreur pédagogiques (ligne/clé fautive).
3. **merge** → applique héritage add-only (root → suite → test). Les listes se **concatènent** (on n’efface jamais).
4. **plan** → développe `matrix` et `repeat` en cas concrets, prépare les contextes initiaux (seed, vars).
5. **run (par test)**

   * setup (avec timeout dédié)
   * exec (subprocess, `asyncio`, `timeout`, *kill process-group*, `ulimit` CPU/mémoire/fichiers)
   * collecte `stdout/stderr` (+ fichiers)
   * pipeline **filters → checks** pour chaque flux (ordre strict)
   * teardown (timeout dédié)
6. **report** (Rich + exports optionnels JUnit/Annotations).
7. **exit code** du runner = nombre d’échecs > 0 ? 1 : 0.

## Points clés d’implémentation

* **PCRE** : utiliser le module `regex` (API proche de `re`, features PCRE-like).

  * Supporter la *syntaxe compacte* façon Perl :

    * `match: "m/\\b\\d+\\.\\d+\\.\\d+\\b/im"`
    * `sub:   "s/\\s+//g"`
  * Et la *forme canonique* :

    * `match: { regex: "\\b\\d+\\.\\d+\\.\\d+\\b", flags: "im" }`
    * `sub:   { regex: "\\s+", repl: "", flags: "g" }`
* **Deux formes pour les checks** (tu y tiens, parfait) :

  * compacte: `- contains: "Version"`
  * canonique:

    ```yaml
    - contains:
        value: "Version"
        explain: "La sortie doit contenir « Version »"
    ```

  Pydantic convertit tout en interne vers `{type, value, explain?}`.
* **Templating minimal** : parser `{{ … }}` **maison**, gestion `x++`/`++x` en pré-processing du contexte (pas de Jinja).
* **Évaluations** :

  * `check_eval` (assertion booléenne) et `map_eval` (transformation) via `simpleeval`/`asteval` **sandboxés** : pas d’I/O, builtins filtrés, *timeout microscopique* via watchdog.
* **capture** : simple et sans nom de groupe (comme tu le souhaites)

  ```yaml
  - capture:
      regex: "(\\d+)"
      group: 1      # défaut 1
      tests:
        - lt: 4
  ```

  (pas de “as:”, on reste minimal).
* **files** : si une clé fichier est mentionnée → existence **implicite** exigée, donc on lit son contenu et on applique `filters`+`checks` identiques aux streams.

  ```yaml
  files:
    "foo.yml":
      filters: [ { trim: {} } ]
      checks:
        - contains: "bar"
  ```

## Commandes CLI

* `baygon run tests.yml [--only "Suite::Test"] [--report junit.xml] [--seed 42] [--fail-fast]`
* `baygon lint tests.yml` (validation + suggestions)
* `baygon explain tests.yml` (affiche la config *après merge* et expansion)
* `baygon list tests.yml` (arbre des tests)
* `baygon plugins` (liste et vérifie les plugins installés)

## Plugins

* Découverte via **entry points** : `baygon.filters` et `baygon.checks`.
* Chargement paresseux; si un nom est inconnu → erreur *guidée* :

  > `Unknown filter 'normalize_uuids'. Peut-être un plugin tiers ? Essayez: pip install baygon-normalize-uuids`
  > (avec *fuzzy matching* type `difflib.get_close_matches`).

# 2) Technologies

* **Langage** : Python 3.11+ (pattern matching, speed, `tomllib` si besoin).
* **CLI** : **Typer** (ergonomie moderne, basé sur Click) **ou** Click pur. Je te conseille **Typer**.
* **Validation & normalisation** : **Pydantic v2** (parfait pour supporter compact/canonique et générer un JSON Schema public).
* **YAML/JSON** : `pyyaml` (lecture) ; pas besoin de préserver les commentaires.
* **Regex PCRE-like** : `regex`.
* **Subprocess** : `asyncio.create_subprocess_exec` + `signal`, `os.setsid`/`start_new_session=True` pour tuer l’arbre; `resource` (POSIX) pour **ulimits**.
* **Sandbox éval** : `simpleeval` (ou `asteval`) avec env ultra restreint.
* **Sortie console** : **Rich** (tables, panels, diffs, highlights).
* **Exports CI** : JUnit XML (lib simple ou maison) + **GitHub Annotations** (format `::error file=…::msg`).
* **Tests du projet** : `pytest` (+ `pytest-asyncio`).
* **Typage** : `mypy` + `ruff` (lint/format).
* **Packaging** : `hatchling` ou `pdm`; plugins via entry points.

# 3) Documentation

* **mkdocs-material** : rapide, élégant, search intégré.

  * `mkdocstrings[python]` pour API auto.
  * `mike` pour versionner la doc.
  * `mkdocs-git-revision-date-localized-plugin` (dates), `mkdocs-awesome-pages-plugin` (nav).
  * Exemples copiables, blocs “⚠️ Attention” / “💡 Astuce”.
* Arbo doc:

  * **Getting Started** (install, premier test)
  * **La DSL** (compacte vs canonique, tableau de correspondance)
  * **Héritage/merge (add-only)** avec schémas
  * **Filters & Checks** (référence complète + perl-like `m//` & `s///`)
  * **Templating & x++**
  * **Sandbox & ressources** (timeouts/ulimits)
  * **Plugins** (comment en écrire/installer)
  * **CI** (GitHub Actions, exemples)
  * **FAQ / Troubleshooting**
  * **Exemples** (tp C/C++/Python)

---

## ⚖️ Sur le nom “Baygon”

“Baygon” est une **marque déposée** mondialement pour des insecticides, appartenant à **S. C. Johnson & Son, Inc.** (acquise à Bayer). On trouve plusieurs enregistrements et litiges TTAB autour de ce mot. Cela signifie que, même dans une autre classe (logiciels), tu t’exposes à un **risque de confusion/dilution** (c’est une marque connue). Je ne peux pas donner de conseil juridique, mais *précaution maximale* : choisir un autre nom (ou un dérivé sans risque). Réfs : marque US chez SC Johnson et pages publiques indiquant la propriété actuelle. ([Justia Trademarks][1])

Idées alternatives (même vibe) : **“Begone”**, **“Bégone”**, **“Bagon”**, **“Bygone”** (jeu sur “be gone”), **“Bagonet”**, **“Bagoon”**, **“Beegone”**. Si tu tiens au clin d’œil, assure-toi au minimum d’un **usage non-conflictuel** (vérifier classes/localités) et d’éviter tout branding visuel/sonore évoquant l’insecticide.

---

### Mini-checklist de démarrage

* [ ] Initialiser `schema.py` (Pydantic) avec parse compact/canonique + JSON Schema.
* [ ] Implémenter `regex` Perl-like `m//flags` & `s///flags` (parser simple).
* [ ] `merge.py` (add-only), `plan.py` (matrix + repeat), `context.py` (x++/++x).
* [ ] `exec.py` (asyncio + ulimit + kill-tree + encodage).
* [ ] `pipeline.py` (filters→checks, capture, check_eval/map_eval).
* [ ] `reporters/rich_reporter.py` (UX étudiante : diff propre, messages `explain`).
* [ ] `cli.py` (run/lint/explain/list/plugins).
* [ ] `examples/` + `mkdocs` avec “Getting Started”.

Si tu veux, je peux t’esquisser `schema.py` (Pydantic v2) et `exec.py` minimal pour poser les fondations.

[1]: https://trademarks.justia.com/856/81/baygon-85681313.html?utm_source=chatgpt.com "BAYGON Trademark of S. C. Johnson & Son, Inc."

---

Typer me semble un peu trop "lolcat" dans le style, je préfère une syntaxe pour les cli propre et sobre par défaut. Click me semble bien même si c'est pain in the ass pour faire des tests fonctionnels avec pytest. L'idée des reporters est excellent et la notion de plugins.

Python 3.11 c'est bien, peut-être que 3.10 est encore important ? Voir si compatible ou pas on peut partir 3.11+ si tu penses que c'est mieux. tomllib je hais toml c'est une syntaxe infame. YAML ou JSON c'est 100x mieux mais mon c'est mon avis personnel.

YAML on peut utiliser ruaml pour extraire éventuellement le numéro de ligne de l'erreur lors du pars avec pydanric ce qui peut être utile. pour json je ne sais pas si c'est possible.

hatchling ou pdm je ne connais pas mais c'est éventuellement quelque chose qui pourrait être bien !

Va pour mkdocs-material pour la doc. Je vais prendre le risque et garder baygon pour l'instant.

Commençons à coder, proposes moi le schema.py pour parser la syntaxe, on va ensuite faire des tests unitaires pour consolider la syntaxe. Elle risque d'être compliquée avec les coercisions possibles.

Il faut résoudre le problème de comment accepter une syntaxe permissive (depuis un YAML ou un json) avec les coecisions, et une syntaxe canonique plus verbeuse. Soit ca peut être fait avec un seul schéma soit on voit les choses en deux étapes. A toi de voir.

Première étape, propose moi le fichier schema.py
