import re
from difflib import SequenceMatcher


GENERIC_WORDS = {
    "the",
    "hotel",
    "hotels",
    "resort",
    "resorts",
    "by",
    "at",
}


CITY_ALIASES = {
    "delhi": "new delhi",
    "south goa": "goa",
}


AREA_ALIASES = {
    "chanakya puri": "chanakyapuri",
    "pichola": "lake pichola",
}


def normalize_text(value):
    value = (
        value
        or ""
    ).lower().strip()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    words = [
        word
        for word in value.split()
        if word not in GENERIC_WORDS
    ]

    return " ".join(words)


def normalize_city(city):
    city = normalize_text(city)

    return CITY_ALIASES.get(
        city,
        city,
    )


def normalize_area(area):
    area = normalize_text(area)

    return AREA_ALIASES.get(
        area,
        area,
    )


def token_set(value):
    return set(
        normalize_text(value).split()
    )


def token_overlap(left, right):
    left_tokens = token_set(left)
    right_tokens = token_set(right)

    if (
        not left_tokens
        or not right_tokens
    ):
        return 0.0

    intersection = (
        left_tokens
        & right_tokens
    )

    smaller_set_size = min(
        len(left_tokens),
        len(right_tokens),
    )

    return (
        len(intersection)
        / smaller_set_size
    )


def sequence_similarity(left, right):
    return SequenceMatcher(
        None,
        normalize_text(left),
        normalize_text(right),
    ).ratio()


def name_similarity(left, right):
    overlap_score = token_overlap(
        left,
        right,
    )

    sequence_score = sequence_similarity(
        left,
        right,
    )

    return max(
        overlap_score,
        sequence_score,
    )


def area_similarity(left, right):
    left = normalize_area(left)
    right = normalize_area(right)

    if left == right:
        return 1.0

    return max(
        token_overlap(left, right),
        sequence_similarity(left, right),
    )


def offers_match(
    left,
    right,
    threshold=0.72,
):
    left_city = normalize_city(
        left.city
    )

    right_city = normalize_city(
        right.city
    )

    if left_city != right_city:
        return False

    name_score = name_similarity(
        left.hotel_name,
        right.hotel_name,
    )

    area_score = area_similarity(
        left.area,
        right.area,
    )

    rating_score = 0.0

    if (
        left.rating is not None
        and right.rating is not None
    ):
        rating_difference = abs(
            left.rating
            - right.rating
        )

        rating_score = max(
            0.0,
            1.0 - rating_difference,
        )

    stars_score = 0.0

    if (
        left.stars is not None
        and right.stars is not None
        and left.stars == right.stars
    ):
        stars_score = 1.0

    combined_score = (
        name_score * 0.55
        + area_score * 0.25
        + rating_score * 0.10
        + stars_score * 0.10
    )

    return (
        name_score >= 0.60
        and combined_score >= threshold
    )
