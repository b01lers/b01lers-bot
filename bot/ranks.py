from typing import List

RANK_NAMES = [
    "🐟 Phish Food",
    "📜 Script Kiddie",
    "⌨️ /r/masterhacker",
    "</> Inspector of Elements",
    "❌ Cross-Site Scripter",
    "💫 Path Explorer",
    "🎩 White Hat",
    "🛠️ Pwn Tool",
    "🤫 Bad Actor",
    "🐣 Fuzzer Duckling",
    "🦦 ShellMammal",
    "👾 Anti-Anti Virus",
    "💻 Not an Enigma",
    "🐚 Shell Popper",
    "💸 Bounty Hunter",
    "💼 Edge Case",
    "🖥️ Gibson Crasher",
    "🔥 Intrusion Creation System",
    "🍦 Zero Cool",
    "🏳️‍🌈 1337",
]
RANK_COLORS = [
    0x7B334C,
    0xA14D55,
    0xC77369,
    0xE3A084,
    0xF2CB9B,
    0xD37B86,
    0xAF5D8B,
    0x804085,
    0x5B3374,
    0x412051,
    0x5C486A,
    0x621748,
    0x942C4B,
    0xE06B51,
    0xF2A561,
    0xB1D480,
    0x658D78,
    0xD1C7EB,
    0xE055B8,
]
RANK_COUNT = len(RANK_NAMES)


def generate_ranks(maximum: int, steps: int) -> List[int]:
    """
    Generate a list of ranks that get harder to obtain as they approach the maximum

    :param maximum: The maximum rank
    :param steps: The number of ranks to generate
    """
    ranks = []

    for i in range(steps):
        ranks += [maximum]
        maximum = int(maximum * 0.75)

    return list(reversed(ranks))


def get_rank(points: int, cutoffs: List[int]) -> int:
    """
    Get the rank for a given number of points

    :param points: The number of points
    :param cutoffs: The list of cutoffs
    """
    rank = 0
    for i, cutoff in enumerate(cutoffs):
        if points < cutoff:
            if i == 0:
                break
            else:
                rank = i - 1
                break
    else:
        rank = RANK_COUNT - 1

    return rank