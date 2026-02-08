"""Line wrapping helpers for PDF output."""


def _wrap_pdf_lines(pdf, text, max_width):
    """Wrap text into lines that fit within the PDF width."""
    wrapped_lines = []
    for raw_line in text.splitlines():
        if raw_line.strip() == "":
            wrapped_lines.append("")
            continue

        words = raw_line.split()
        current = ""

        for word in words:
            candidate = word if current == "" else f"{current} {word}"
            if pdf.get_string_width(candidate) <= max_width:
                current = candidate
                continue

            if current:
                wrapped_lines.append(current)
                current = ""

            while pdf.get_string_width(word) > max_width:
                part = ""
                for ch in word:
                    if pdf.get_string_width(part + ch) <= max_width:
                        part += ch
                    else:
                        break
                if part == "":
                    part = word[:1]
                wrapped_lines.append(part)
                word = word[len(part):]

            current = word

        if current:
            wrapped_lines.append(current)

    return wrapped_lines


def _wrap_pdf_lines_with_first_width(pdf, text, first_width, max_width):
    """Wrap text with a custom first-line width and full width afterwards."""
    wrapped_lines = []
    words = text.split()
    current = ""
    current_width = first_width

    for word in words:
        candidate = word if current == "" else f"{current} {word}"
        if pdf.get_string_width(candidate) <= current_width:
            current = candidate
            continue

        if current:
            wrapped_lines.append(current)
            current = ""
            current_width = max_width

        while pdf.get_string_width(word) > current_width:
            part = ""
            for ch in word:
                if pdf.get_string_width(part + ch) <= current_width:
                    part += ch
                else:
                    break
            if part == "":
                part = word[:1]
            wrapped_lines.append(part)
            word = word[len(part):]
            current_width = max_width

        current = word

    if current:
        wrapped_lines.append(current)

    return wrapped_lines


def _count_wrapped_lines(pdf, text, max_width):
    return len(_wrap_pdf_lines(pdf, text, max_width))


def _count_wrapped_lines_first_width(pdf, text, first_width, max_width):
    return len(_wrap_pdf_lines_with_first_width(pdf, text, first_width, max_width))
