"""
Schema et normalisation de la DSL "baygon" (v1)

- Accepte une syntaxe **permissive** (compacte) depuis YAML/JSON
- Normalise en une forme **canonique** interne
- Indépendant de l'I/O (pas de lecture de fichiers ici)

Points clés:
- Deux formes pour checks/filters: compacte (`contains: "x"`) et canonique
  (`contains: { value: "x", explain: "..." }`).
- PCRE-like support: `m/.../flags` et `s/.../.../flags` (via module `regex` côté exécution ;
  ici on stocke `regex`, `repl`, `flags`).
- Mix **filters** et **checks** dans l'ordre de `stdout`/`stderr`/`files.<name>`.
- `capture` sans nom symbolique; `group` par défaut à 1.
- `eval` scindé en `check_eval` (assertion) et `map_eval` (filtre/transform).
- On **évite les revalidations Pydantic** en stockant des objets déjà normalisés
  (les champs `stdout`/`stderr`/`filters`/`files.*.ops` sont typés `List[Any]`).
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import BaseModel, Field, ValidationError, model_validator
import re

# ---------------------------------------------------------------------------
# Utilitaires
# ---------------------------------------------------------------------------

_PERL_M = re.compile(r"^m\/(.*)\/([a-zA-Z]*)$")
_PERL_S = re.compile(r"^s\/(.*)\/(.*)\/([a-zA-Z]*)$")


def _parse_perl_like(pattern: str) -> Tuple[str, str, Optional[str]]:
    """Parse une regex Perl-like:
    - match:  "m/<regex>/<flags>"  → ("m", regex, flags)
    - sub:    "s/<regex>/<repl>/<flags>" → ("s", "regex:::repl", flags)
    - sinon:  ("", pattern, None)
    """
    m = _PERL_M.match(pattern)
    if m:
        rx, flags = m.group(1), m.group(2) or None
        return ("m", rx, flags)
    s = _PERL_S.match(pattern)
    if s:
        rx, repl, flags = s.group(1), s.group(2), s.group(3) or None
        return ("s", f"{rx}:::{repl}", flags)
    return ("", pattern, None)


def _as_str_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v]
    return [str(v)]


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

class FilterBase(BaseModel):
    kind: Literal["trim", "lower", "upper", "sub", "map_eval"]


class FTrim(FilterBase):
    kind: Literal["trim"] = "trim"


class FLower(FilterBase):
    kind: Literal["lower"] = "lower"


class FUpper(FilterBase):
    kind: Literal["upper"] = "upper"


class FSub(FilterBase):
    kind: Literal["sub"] = "sub"
    regex: str
    repl: str = ""
    flags: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        # Formes admises:
        # - "s/REGEX/REPL/gmi"
        # - { regex: "REGEX", repl: "REPL", flags: "gmi" }
        if isinstance(v, str):
            kind, packed, flags = _parse_perl_like(v)
            if kind == "s":
                rx, repl = packed.split(":::", 1)
                return {"regex": rx, "repl": repl, "flags": flags}
            # String non perl-like → sub avec repl vide (suppression)
            return {"regex": v, "repl": "", "flags": None}
        return v


class FMapEval(FilterBase):
    kind: Literal["map_eval"] = "map_eval"
    expr: str = Field(..., description="Expression sûre, renvoie une string")


Filter = Union[FTrim, FLower, FUpper, FSub, FMapEval]


def parse_filter(obj: Any) -> Filter:
    """Accepte:
    - { trim: {} }
    - { sub: "s/\s+//g" }
    - { sub: { regex: "...", repl: "...", flags: "gmi" } }
    - { lower: {} }, { upper: {} }, { map_eval: "expr" } ou dict canonique
    """
    if not isinstance(obj, dict) or len(obj) != 1:
        raise ValueError("Chaque filtre doit être un objet à une seule clé")
    key, val = next(iter(obj.items()))
    if key == "trim":
        return FTrim()
    if key == "lower":
        return FLower()
    if key == "upper":
        return FUpper()
    if key == "sub":
        return FSub.model_validate(val)
    if key == "map_eval":
        if isinstance(val, str):
            return FMapEval(expr=val)
        if isinstance(val, dict) and "expr" in val:
            return FMapEval(**val)
    raise ValueError(f"Filtre inconnu: {key}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

class CheckBase(BaseModel):
    kind: Literal[
        "match",
        "contains",
        "not_contains",
        "equals",
        "not_equals",
        "lt",
        "lte",
        "gt",
        "gte",
        "check_eval",
        "capture",
    ]
    explain: Optional[str] = None


class CMatch(CheckBase):
    kind: Literal["match"] = "match"
    regex: str
    flags: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        if isinstance(v, str):
            kind, rx, flags = _parse_perl_like(v)
            if kind == "m":
                return {"regex": rx, "flags": flags}
            return {"regex": v, "flags": None}
        return v


class CString(CheckBase):
    value: str

    @model_validator(mode="before")
    @classmethod
    def _coerce_base(cls, v: Any) -> Any:
        if isinstance(v, dict):
            if "explaination" in v and "explain" not in v:
                v = {**v, "explain": v["explaination"]}
            if "explanation" in v and "explain" not in v:
                v = {**v, "explain": v["explanation"]}
            if "value" in v:
                v["value"] = str(v["value"])  # coercion string
                return v
        return {"value": str(v)}


class CContains(CString):
    kind: Literal["contains"] = "contains"


class CNotContains(CString):
    kind: Literal["not_contains"] = "not_contains"


class CEquals(CString):
    kind: Literal["equals"] = "equals"


class CNotEquals(CString):
    kind: Literal["not_equals"] = "not_equals"


class CNumber(CheckBase):
    value: float

    @model_validator(mode="before")
    @classmethod
    def _coerce_num(cls, v: Any) -> Any:
        if isinstance(v, dict):
            if "explaination" in v and "explain" not in v:
                v = {**v, "explain": v["explaination"]}
            if "explanation" in v and "explain" not in v:
                v = {**v, "explain": v["explanation"]}
            if "value" in v:
                return {**v, "value": float(v["value"])}
        return {"value": float(v)}


class CLt(CNumber):
    kind: Literal["lt"] = "lt"


class CLte(CNumber):
    kind: Literal["lte"] = "lte"


class CGt(CNumber):
    kind: Literal["gt"] = "gt"


class CGte(CNumber):
    kind: Literal["gte"] = "gte"


class CCheckEval(CheckBase):
    kind: Literal["check_eval"] = "check_eval"
    expr: str

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"expr": v}
        if isinstance(v, dict):
            if "explaination" in v and "explain" not in v:
                v = {**v, "explain": v["explaination"]}
            if "explanation" in v and "explain" not in v:
                v = {**v, "explain": v["explanation"]}
        return v


class CCapture(CheckBase):
    kind: Literal["capture"] = "capture"
    regex: str
    flags: Optional[str] = None
    group: int = 1
    # on accepte n'importe quelle forme puis on normalise en after-validator
    tests: List[Any] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        if isinstance(v, dict):
            out = dict(v)
            if "explaination" in out and "explain" not in out:
                out["explain"] = out.pop("explaination")
            if "explanation" in out and "explain" not in out:
                out["explain"] = out.pop("explanation")
            if "regex" in out and isinstance(out["regex"], str):
                kind, rx, flags = _parse_perl_like(out["regex"])  # support m//
                if kind == "m":
                    out["regex"], out["flags"] = rx, flags
            return out
        return v

    @model_validator(mode="after")
    def _coerce_tests(self):
        norm: List[CheckBase] = []
        for item in self.tests:
            if isinstance(item, CheckBase):
                norm.append(item)
            else:
                norm.append(parse_check(item))
        self.tests = norm
        return self


Check = Union[
    CMatch,
    CContains,
    CNotContains,
    CEquals,
    CNotEquals,
    CLt,
    CLte,
    CGt,
    CGte,
    CCheckEval,
    CCapture,
]


def parse_check(obj: Any) -> Check:
    if not isinstance(obj, dict) or len(obj) != 1:
        raise ValueError("Chaque check doit être un objet à une seule clé")
    key, val = next(iter(obj.items()))
    if key == "match":
        return CMatch.model_validate(val)
    if key == "contains":
        return CContains.model_validate(val)
    if key == "not_contains":
        return CNotContains.model_validate(val)
    if key == "equals":
        return CEquals.model_validate(val)
    if key == "not_equals":
        return CNotEquals.model_validate(val)
    if key == "lt":
        return CLt.model_validate(val)
    if key == "lte":
        return CLte.model_validate(val)
    if key == "gt":
        return CGt.model_validate(val)
    if key == "gte":
        return CGte.model_validate(val)
    if key == "check_eval":
        return CCheckEval.model_validate(val)
    if key == "capture":
        return CCapture.model_validate(val)

    raise ValueError(f"Check inconnu: {key}")


# ---------------------------------------------------------------------------
# Stream ops (mix filters & checks)
# ---------------------------------------------------------------------------

StreamOp = Union[Filter, Check]


def parse_stream_ops(seq: Any) -> List[StreamOp]:
    if seq is None:
        return []
    if not isinstance(seq, list):
        raise ValueError("Un flux doit être une liste d'opérations (filters/checks)")
    out: List[StreamOp] = []
    for item in seq:
        if not isinstance(item, dict) or len(item) != 1:
            raise ValueError("Chaque opération doit être un objet à une seule clé")
        k = next(iter(item.keys()))
        if k in {"trim", "lower", "upper", "sub", "map_eval"}:
            out.append(parse_filter(item))
        else:
            out.append(parse_check(item))
    return out


# ---------------------------------------------------------------------------
# Exécution / Contexte
# ---------------------------------------------------------------------------

class ExecConfig(BaseModel):
    cmd: Union[str, List[str]]
    timeout: Optional[float] = None
    stdin: Optional[Union[str, List[str]]] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    cwd: Optional[str] = None
    shell: bool = False

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            raise TypeError("exec doit être un objet")
        v = dict(v)
        if "args" in v and v["args"] is not None:
            v["args"] = [str(x) for x in _as_str_list(v["args"])]
        else:
            v["args"] = []
        if "stdin" in v and v["stdin"] is not None:
            if isinstance(v["stdin"], (list, tuple)):
                v["stdin"] = [str(x) for x in v["stdin"]]
            elif not isinstance(v["stdin"], str):
                v["stdin"] = str(v["stdin"])  # fallback
        return v


class SetupStep(BaseModel):
    kind: Literal["run", "eval"]
    value: str

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        if isinstance(v, dict) and len(v) == 1:
            k, val = next(iter(v.items()))
            if k in ("run", "eval"):
                return {"kind": k, "value": str(val)}
        raise TypeError("Une étape de setup/teardown doit être { run: ... } ou { eval: ... }")


# ---------------------------------------------------------------------------
# TestCase & FileSpec
# ---------------------------------------------------------------------------

class FileSpec(BaseModel):
    # Objets déjà normalisés → éviter revalidation
    ops: List[Any] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _coerce(cls, v: Any) -> Any:
        if isinstance(v, list):
            return {"ops": parse_stream_ops(v)}
        if isinstance(v, dict):
            if "ops" in v and isinstance(v["ops"], list):
                v = dict(v)
                v["ops"] = parse_stream_ops(v["ops"])
                return v
            if "filters" in v or "checks" in v:
                filters = parse_stream_ops(v.get("filters") or [])
                checks = parse_stream_ops(v.get("checks") or [])
                return {"ops": [*filters, *checks]}
        raise ValueError("files.<name> doit être une liste d'opérations ou {ops:[...]}" )


class TestCase(BaseModel):
    __test__ = False
    name: str
    description: Optional[str] = None

    tests: Optional[List["TestCase"]] = None

    # Objets déjà normalisés (pas de revalidation Union)
    filters: List[Any] = Field(default_factory=list)
    setup: List[SetupStep] = Field(default_factory=list)
    teardown: List[SetupStep] = Field(default_factory=list)

    stdin: Optional[Union[str, List[str]]] = None
    args: List[str] = Field(default_factory=list)
    exit: Optional[int] = None
    repeat: int = 1

    stdout: List[Any] = Field(default_factory=list)
    stderr: List[Any] = Field(default_factory=list)

    files: Dict[str, FileSpec] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _pre(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            raise TypeError("Chaque test doit être un objet")
        v = dict(v)
        if "args" in v and v["args"] is not None:
            v["args"] = [str(x) for x in _as_str_list(v["args"])]
        else:
            v["args"] = []
        if "stdout" in v:
            v["stdout"] = parse_stream_ops(v.get("stdout") or [])
        if "stderr" in v:
            v["stderr"] = parse_stream_ops(v.get("stderr") or [])
        if "filters" in v:
            v["filters"] = [parse_filter(x) for x in (v.get("filters") or [])]
        if "files" in v and isinstance(v["files"], dict):
            files_norm: Dict[str, FileSpec] = {}
            for fname, spec in v["files"].items():
                files_norm[fname] = FileSpec.model_validate(spec)
            v["files"] = files_norm
        if "setup" in v:
            v["setup"] = [SetupStep.model_validate(x) for x in (v.get("setup") or [])]
        if "teardown" in v:
            v["teardown"] = [SetupStep.model_validate(x) for x in (v.get("teardown") or [])]
        return v


TestCase.model_rebuild()


# ---------------------------------------------------------------------------
# Racine
# ---------------------------------------------------------------------------

class Spec(BaseModel):
    version: int = 1
    exec: ExecConfig

    filters: List[Any] = Field(default_factory=list)

    tests: List[TestCase]

    @model_validator(mode="before")
    @classmethod
    def _pre(cls, v: Any) -> Any:
        if not isinstance(v, dict):
            raise TypeError("Le document racine doit être un objet")
        v = dict(v)
        if "filters" in v:
            v["filters"] = [parse_filter(x) for x in (v.get("filters") or [])]
        return v


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def normalize_spec(data: Dict[str, Any]) -> Spec:
    """Valide et normalise un dict (issu YAML/JSON) vers un modèle **canonique**.
    Lève `pydantic.ValidationError` en cas d'erreur.
    """
    return Spec.model_validate(data)


__all__ = [
    "Spec",
    "ExecConfig",
    "TestCase",
    "Filter",
    "Check",
    "StreamOp",
    "normalize_spec",
]
