def split_content(content: str, max_length: int) -> list[str]:
    """
    Split text into chunks at word boundaries (assumes content > max_length)

    If no space found, split at `max_length`
    """
    split_point = content.rfind(" ", 0, max_length)
    split_point = max_length if split_point == -1 else split_point

    chunk = content[:split_point]
    remaining = content[split_point:].lstrip()

    if len(remaining) <= max_length:
        return [chunk, remaining] if remaining else [chunk]

    return [chunk, *split_content(remaining, max_length)]

