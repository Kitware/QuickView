TYPE_COLORS = [
    "brown",
    "amber",
    "cyan",
    "purple",
    "blue-gray",
    "green",
    "deep-orange",
    "indigo",
    "pink",
    "teal",
    "gray",
    "red",
]


def get_type_color(index: int) -> str:
    return TYPE_COLORS[index % len(TYPE_COLORS)]
