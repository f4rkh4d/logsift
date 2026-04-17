"""Follow mode: tail -f style streaming."""

from __future__ import annotations

import os
import time
from typing import Iterator, List


def follow_files(paths: List[str], poll_interval: float = 0.25) -> Iterator[str]:
    """Yield new lines from one or more files as they are appended.

    Starts at current EOF. Handles rotation by reopening when inode changes or
    size shrinks.
    """
    handles = {}
    for p in paths:
        try:
            f = open(p, "r")
            f.seek(0, os.SEEK_END)
            st = os.fstat(f.fileno())
            handles[p] = {"f": f, "inode": st.st_ino, "size": st.st_size}
        except OSError:
            continue

    try:
        while True:
            any_line = False
            for p, h in list(handles.items()):
                f = h["f"]
                # rotation check
                try:
                    st = os.stat(p)
                    if st.st_ino != h["inode"] or st.st_size < h["size"]:
                        f.close()
                        nf = open(p, "r")
                        handles[p] = {"f": nf, "inode": st.st_ino, "size": 0}
                        f = nf
                except OSError:
                    pass

                while True:
                    line = f.readline()
                    if not line:
                        break
                    any_line = True
                    h["size"] = f.tell()
                    yield line

            if not any_line:
                time.sleep(poll_interval)
    finally:
        for h in handles.values():
            try:
                h["f"].close()
            except Exception:
                pass
