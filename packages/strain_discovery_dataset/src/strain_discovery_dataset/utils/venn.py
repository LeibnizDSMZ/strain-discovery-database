from itertools import combinations


def calculate_venn_stats(
    source_names: list[str], sources: dict[str, set[str]], /
) -> dict[str, int]:
    venn_stats = {}

    for com in range(2, len(source_names) + 1):
        for combo in combinations(source_names, com):
            key = "|".join(sorted(combo))
            intersection = set.intersection(*[sources[src] for src in combo])
            venn_stats[key] = len(intersection)

    return venn_stats


def create_venn_headers(source_names: list[str], /) -> list[str]:
    return [
        "|".join(sorted(combo))
        for com in range(2, len(source_names) + 1)
        for combo in combinations(source_names, com)
    ]
