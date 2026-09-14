import math


def cosine_similarity(
    a: list[float],
    b: list[float],
) -> float:
    dot_product = sum(
        x * y for x, y in zip(a, b)
    )

    norm_a = math.sqrt(
        sum(x * x for x in a)
    )

    norm_b = math.sqrt(
        sum(y * y for y in b)
    )

    return dot_product / (norm_a * norm_b)