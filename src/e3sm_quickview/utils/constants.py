VAR_HEADERS = [
    {"title": "Name", "align": "start", "key": "name", "sortable": True},
    {"title": "Type", "align": "start", "key": "type", "sortable": True},
]

TRACK_STEPS = {
    "timestamps": "time_idx",
    "interfaces": "interface_idx",
    "midpoints": "midpoint_idx",
}

TRACK_ENTRIES = {
    "timestamps": {"title": "Time", "value": "timestamps"},
    "midpoints": {"title": "Layer Midpoints", "value": "midpoints"},
    "interfaces": {"title": "Layer Interfaces", "value": "interfaces"},
}
