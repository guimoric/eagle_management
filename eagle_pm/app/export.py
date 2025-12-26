from __future__ import annotations

import csv
import io
from typing import Iterable, List


def rows_to_csv(headers: List[str], rows: Iterable[Iterable]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()
