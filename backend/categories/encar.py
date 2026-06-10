from typing import Any

LEVEL_MAKE = "make"
LEVEL_MODEL_GROUP = "model_group"
LEVEL_MODEL = "model"

ENCAR_BASE_QUERY = "(And.Hidden.N._.CarType.A.)"
ENCAR_NODES = {
    LEVEL_MAKE: "Manufacturer",
    LEVEL_MODEL_GROUP: "ModelGroup",
    LEVEL_MODEL: "Model",
}


def build_encar_query(category: dict[str, Any] | None = None) -> str:
    if not category:
        return ENCAR_BASE_QUERY

    make = category.get("make_code")
    model_group = category.get("model_group_code")
    model = category.get("model_code")
    query = "(And.Hidden.N._.CarType.A"

    if make:
        query += f"._.Manufacturer.{make}"
    if model_group:
        query += f"._.ModelGroup.{model_group}"
    if model:
        query += f"._.Model.{model}"

    return f"{query}.)"


def extract_encar_categories(data: dict, level: str) -> list[dict]:
    node = _find_node((data.get("iNav") or {}).get("Nodes", []), ENCAR_NODES[level])
    facets = (node or {}).get("Facets", [])
    return [_build_category(facet, level) for facet in facets if _facet_count(facet) > 0]


def _find_node(nodes: list[dict], name: str) -> dict | None:
    for node in nodes:
        if node.get("Name") == name:
            return node

        found = _find_in_facets(node.get("Facets", []), name)
        if found:
            return found

    return None


def _find_in_facets(facets: list[dict], name: str) -> dict | None:
    for facet in facets:
        nodes = ((facet.get("Refinements") or {}).get("Nodes") or [])
        found = _find_node(nodes, name)
        if found:
            return found
    return None


def _build_category(facet: dict, level: str) -> dict:
    return {
        "level": level,
        "name": str(facet.get("DisplayValue") or facet.get("Value") or ""),
        "code": _extract_code(facet, ENCAR_NODES[level]),
        "count": _facet_count(facet),
        "raw_data": facet,
    }


def _extract_code(facet: dict, node_name: str) -> str:
    expression = str(facet.get("Expression") or "")
    prefix = f"{node_name}."
    if expression.startswith(prefix) and expression.endswith("."):
        return expression[len(prefix):-1]
    return str(facet.get("Value") or facet.get("DisplayValue") or "")


def _facet_count(facet: dict) -> int:
    try:
        return int(facet.get("Count") or 0)
    except (TypeError, ValueError):
        return 0
