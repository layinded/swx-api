def summarize_departures_speech(stop_name: str, departures: str) -> str:
    """
    Generate a short, speech-friendly summary from raw departure data.

    Args:
        stop_name (str): Name of the stop (for use in the response).
        departures (str): Formatted list of departures (multi-line).

    Returns:
        str: A natural one-liner summary highlighting the next 1–2 departures,
             suitable for voice assistants or chatbot replies.
    """
    if not departures:
        return f"No upcoming departures from {stop_name}."

    lines = [line.strip() for line in departures.splitlines() if "Line" in line]
    if not lines:
        return f"There are departures from {stop_name}, but the line details are unavailable."

    return f"The next departures from {stop_name} are: {'; '.join(lines[:2])}."
