from lxml import etree


def update_svg(path: str, stats: dict) -> None:
    tree = etree.parse(path)
    root = tree.getroot()
    for element_id, value in stats.items():
        _update_field(root, element_id, value)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _update_field(root, element_id: str, new_value) -> None:
    new_text = f"{new_value:,}" if isinstance(new_value, int) else str(new_value)

    value_el = root.find(f".//*[@id='{element_id}']")
    if value_el is None:
        return

    dots_el = root.find(f".//*[@id='{element_id}_dots']")
    if dots_el is not None:
        target = len(dots_el.text or "") + len(value_el.text or "")
        dots_el.text = _make_dots(target - len(new_text))

    value_el.text = new_text


def _make_dots(n: int) -> str:
    if n <= 0:
        return ""
    if n == 1:
        return " "
    if n == 2:
        return ". "
    return " " + ("." * (n - 2)) + " "
