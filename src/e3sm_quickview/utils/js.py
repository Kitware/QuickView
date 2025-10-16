def var_count(name):
    return f"variables_selected.filter((v) => v[0] === '{name[0]}').length"


def var_remove(name):
    return (
        f"variables_selected = variables_selected.filter((v) => v[0] !== '{name[0]}')"
    )


def var_title(name):
    return " ".join(["{{", var_count(name), "}}", name.capitalize()])


def is_active(name):
    return f"active_tools.includes('{name}')"
