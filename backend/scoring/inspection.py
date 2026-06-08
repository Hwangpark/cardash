def score_inspection(data: dict, max_points: float) -> float:
    if data.get("isInspectionPrivate"):
        return 0

    score        = float(max_points)
    has_diag     = data.get("hasDiagnosis", False)
    has_insp     = data.get("hasInspection", False)
    rank_counts  = data.get("rankCounts") or {}

    if not has_diag:
        score -= 5

    if has_diag:
        if data.get("diagFrameReplacement"):  score -= 12
        if data.get("diagPanelReplacement"):  score -= 3
        tier = data.get("diagnosisTier", "BASIC")
        if   tier == "PLUSPLUS": score += 4
        elif tier == "PLUS":     score += 2
        return max(0, min(max_points, score))

    if not has_insp:
        return max(0, max_points * 0.5 - 5)

    if rank_counts:
        b   = rank_counts.get("B",   {})
        a   = rank_counts.get("A",   {})
        two = rank_counts.get("TWO", {})
        one = rank_counts.get("ONE", {})

        score -= b.get("X", 0) * 15
        score -= b.get("W", 0) * 12
        score -= a.get("X", 0) * 10
        score -= a.get("W", 0) * 8
        score -= two.get("X", 0) * 4
        score -= two.get("W", 0) * 3
        score -= one.get("X", 0) * 1
        score -= one.get("W", 0) * 2

        corrosion = sum(
            rank_counts.get(r, {}).get("C", 0)
            for r in ("B", "A", "TWO", "ONE")
        )
        score -= corrosion * 2
    else:
        if data.get("hasWelding"):     score -= 10
        if data.get("hasCorrosion"):   score -= 5
        if data.get("hasReplacement"): score -= 2

    return max(0, score)
