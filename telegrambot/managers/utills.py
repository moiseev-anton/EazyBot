def replace_digits_to_emojis(value) -> str:
    s = str(value)
    return "".join(f"{ch}\ufe0f\u20e3" if ch.isdigit() else ch for ch in s)