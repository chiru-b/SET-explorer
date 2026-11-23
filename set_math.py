from itertools import combinations, product


CARDS = list(product(range(3), repeat=4))
BOARD = [card for card in CARDS if card[2:] == (0, 0)]


def quandle(a, b):
    """Compute -a - b modulo 3 for each card attribute."""
    return tuple((-left - right) % 3 for left, right in zip(a, b))


def main():
    sets = [
        (a, b, c)
        for a, b, c in combinations(BOARD, 3)
        if quandle(a, b) == c
    ]

    a, b = (0, 1, 0, 0), (1, 2, 0, 0)
    completion = quandle(a, b)

    assert len(CARDS) == 81
    assert len(BOARD) == 9
    assert len(sets) == 12
    assert completion == (2, 0, 0, 0)

    print(f"Total cards: {len(CARDS)}")
    print(f"Board cards: {len(BOARD)} (color and shading fixed at 0)")
    print(f"SETs on the board: {len(sets)}")
    print(f"{a} and {b} complete to {completion}")


if __name__ == "__main__":
    main()
