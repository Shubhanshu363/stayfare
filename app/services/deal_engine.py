def rank_offers(offers):
    """
    Rank offers using the real effective price.

    Effective price =
    listed price
    + taxes
    - instant discount
    - cashback
    """

    return sorted(
        offers,
        key=lambda offer: offer.effective_price
    )


def best_offer(offers):
    ranked = rank_offers(offers)

    if not ranked:
        return None

    return ranked[0]
