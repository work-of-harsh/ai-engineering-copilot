
from typing import Dict, List


def chunk_document(
    path: str,
    content: str,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> List[Dict[str, object]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size"
        )

    chunks = []
    lines = content.splitlines()

    if not lines:
        return chunks

    current_lines = []
    current_length = 0
    start_line = 1
    index = 0

    while index < len(lines):
        line = lines[index]
        line_length = len(line) + 1

        if current_lines and current_length + line_length > chunk_size:
            chunks.append({
                "path": path,
                "start_line": start_line,
                "end_line": start_line + len(current_lines) - 1,
                "content": "\n".join(current_lines),
            })

            # Keep recent lines for context in the next chunk.
            overlap_lines = []
            overlap_length = 0

            for previous_line in reversed(current_lines):
                size = len(previous_line) + 1

                if overlap_length + size > overlap:
                    break

                overlap_lines.insert(0, previous_line)
                overlap_length += size

            start_line += len(current_lines) - len(overlap_lines)
            current_lines = overlap_lines
            current_length = overlap_length
            continue

        current_lines.append(line)
        current_length += line_length
        index += 1

    if current_lines:
        chunks.append({
            "path": path,
            "start_line": start_line,
            "end_line": start_line + len(current_lines) - 1,
            "content": "\n".join(current_lines),
        })

    return chunks
