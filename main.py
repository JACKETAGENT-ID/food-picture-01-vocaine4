#!/usr/bin/env python3
"""Ship the steaming dim sum photograph for food-picture-01.

Layout: ``image.png`` sits in this directory holding the finished
picture of the bamboo steamer.  Running this module performs three
steps and nothing else:

1. locate the output folder named by ``MAKEFUN_OUTPUT_DIR``;
2. audit the picture against the contest limits -- PNG or JPEG, no
   more than 1 MiB, no dimension beyond 1024 pixels;
3. copy the audited bytes to ``entry.png`` in the output folder and
   read them back to prove the copy is faithful.

The audit reads PNG dimensions from the IHDR chunk and JPEG dimensions
by stepping through segments to the first start-of-frame marker.  All
of it is standard library, and the output is a byte-for-byte copy, so
the result never varies between runs.
"""

import hashlib
import os
import struct
import sys
from pathlib import Path

CEILING_BYTES = 1_048_576
CEILING_SIDE = 1024

MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG = b"\xff\xd8\xff"

# Markers that open a JPEG frame header (baseline through lossless,
# skipping the differential and arithmetic variants without frames).
FRAME_OPENERS = frozenset([
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
])


class AuditFailed(Exception):
    """The picture broke one of the contest limits."""


def iter_jpeg_segments(blob):
    """Yield (marker, segment_bytes) pairs from a JPEG stream."""
    index = 2
    while index + 4 <= len(blob):
        if blob[index] != 0xFF:
            raise AuditFailed("JPEG marker expected at offset %d" % index)
        marker = blob[index + 1]
        span = struct.unpack(">H", blob[index + 2:index + 4])[0]
        if span < 2:
            raise AuditFailed("JPEG segment length %d is invalid" % span)
        yield marker, blob[index + 4:index + 2 + span]
        index += 2 + span


def measure(blob):
    """Return (format, width, height) for an audited payload."""
    if not blob:
        raise AuditFailed("image.png contains nothing")
    if len(blob) > CEILING_BYTES:
        raise AuditFailed(
            "payload of %d bytes exceeds the %d-byte ceiling"
            % (len(blob), CEILING_BYTES)
        )
    if blob.startswith(MAGIC_PNG):
        kind = "png"
        if len(blob) < 24:
            raise AuditFailed("PNG ends before the IHDR chunk completes")
        length = struct.unpack(">I", blob[8:12])[0]
        if blob[12:16] != b"IHDR" or length != 13:
            raise AuditFailed("first PNG chunk is not a 13-byte IHDR")
        width, height = struct.unpack(">II", blob[16:24])
    elif blob.startswith(MAGIC_JPEG):
        kind = "jpeg"
        width = height = None
        for marker, segment in iter_jpeg_segments(blob):
            if marker in FRAME_OPENERS:
                if len(segment) < 5:
                    raise AuditFailed("JPEG frame header is truncated")
                height, width = struct.unpack(">HH", segment[1:5])
                break
        if width is None:
            raise AuditFailed("JPEG has no start-of-frame segment")
    else:
        raise AuditFailed("payload signature is neither PNG nor JPEG")
    if width < 1 or height < 1:
        raise AuditFailed("dimensions %dx%d cannot be real" % (width, height))
    if width > CEILING_SIDE or height > CEILING_SIDE:
        raise AuditFailed(
            "dimensions %dx%d exceed the %d-pixel ceiling"
            % (width, height, CEILING_SIDE)
        )
    return kind, width, height


def entrypoint():
    raw_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if not raw_dir.strip():
        print("error: MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 2
    picture = Path(__file__).resolve().parent / "image.png"
    if not picture.is_file():
        print("error: no bundled image at %s" % picture, file=sys.stderr)
        return 2
    try:
        blob = picture.read_bytes()
        kind, width, height = measure(blob)
    except (OSError, AuditFailed) as problem:
        print("error: %s" % problem, file=sys.stderr)
        return 1
    folder = Path(raw_dir)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / "entry.png"
        target.write_bytes(blob)
        reread = target.read_bytes()
    except OSError as problem:
        print("error: writing the output failed: %s" % problem, file=sys.stderr)
        return 1
    if reread != blob:
        print("error: output copy is not faithful to the picture",
              file=sys.stderr)
        return 1
    stamp = hashlib.sha256(blob).hexdigest()[:16]
    print("delivered %s (%d bytes, %s, %dx%d, sha256:%s)"
          % (target, len(blob), kind, width, height, stamp))
    return 0


if __name__ == "__main__":
    sys.exit(entrypoint())
