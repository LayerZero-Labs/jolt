#!/usr/bin/env python3
"""Prepare untrusted challenge advice from ordered transcript records.

Input JSON has quartet_messages (hex D64/31/10 messages) and position_ranks
(objects with n, pm1, pm2, rank1, rank2). Include only draws routed through
quartet decoding in the first list. The second list contains every rank-valid
candidate inspected on the ordinary decoder, including rejected norm candidates,
in verification order. The guest authenticates all records; this tool is untrusted.
"""
import argparse
import json
from math import comb
from pathlib import Path
import struct


def unrank(rank, n, count):
    if not (0 <= count <= n <= 65536 and 0 <= rank < comb(n, count)):
        raise ValueError("invalid colex rank or subset dimensions")
    result = [0] * count
    upper = n
    for k in range(count, 0, -1):
        lo, hi = k - 1, upper
        while lo + 1 < hi:
            middle = (lo + hi) // 2
            if comb(middle, k) <= rank:
                lo = middle
            else:
                hi = middle
        result[k - 1] = lo
        rank -= comb(lo, k)
        upper = lo
    if rank:
        raise ValueError("nonzero colex remainder")
    return result


def prepare(records):
    quartets = bytearray()
    one_space = comb(64, 31)
    space = one_space * comb(33, 10)
    for text in records.get("quartet_messages", []):
        message = bytes.fromhex(text)
        if not message or len(message) % 16:
            raise ValueError("quartet message must contain whole 128-bit candidates")
        for offset in range(0, len(message), 16):
            candidate = int.from_bytes(message[offset:offset + 16], "little")
            signs, rank = candidate & ((1 << 41) - 1), candidate >> 41
            if rank >= space:
                raise ValueError("quartet candidate has an out-of-range transcript rank")
            rank2, rank1 = divmod(rank, one_space)
            first = unrank(rank1, 64, 31)
            occupied = set(first)
            complement = [i for i in range(64) if i not in occupied]
            second = [complement[i] for i in unrank(rank2, 33, 10)]
            coefficients = [0] * 64
            for i, position in enumerate(first + second):
                coefficients[position] = (1 if i < 31 else 2) * (-1 if signs >> i & 1 else 1)
            words = [0] * 4
            for q in range(16):
                code = sum((coefficients[4*q+i] + 2) * 5**i for i in range(4))
                words[q // 4] |= code << (10 * (q % 4))
            quartets.extend(struct.pack("<4Q", *words))
    positions = bytearray()
    for row in records.get("position_ranks", []):
        n, a, b = (int(row[key]) for key in ("n", "pm1", "pm2"))
        if a < 0 or b < 0 or a + b > n:
            raise ValueError("invalid sparse challenge dimensions")
        subset = unrank(int(row["rank1"]), n, a) + unrank(int(row["rank2"]), n-a, b)
        for start in range(0, len(subset), 4):
            word = sum(position << (16*i) for i, position in enumerate(subset[start:start+4]))
            positions.extend(struct.pack("<Q", word))
    return b"AKITAH02" + struct.pack("<Q", len(quartets)) + quartets + positions


def postcard_bytes(data):
    length = len(data)
    prefix = bytearray()
    while length >= 128:
        prefix.append((length & 127) | 128)
        length >>= 7
    prefix.append(length)
    return prefix + data


def unpack_postcard_bytes(data):
    length = 0
    for offset, byte in enumerate(data[:10]):
        length |= (byte & 127) << (7*offset)
        if byte < 128:
            if offset and byte == 0:
                raise ValueError("noncanonical postcard length")
            body = data[offset+1:]
            if length != len(body):
                raise ValueError("postcard advice length mismatch")
            return body
    raise ValueError("invalid postcard length")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    parser.add_argument("--hints-out", type=Path, required=True)
    parser.add_argument("--base-advice", type=Path)
    parser.add_argument("--advice-out", type=Path)
    args = parser.parse_args()
    if (args.base_advice is None) != (args.advice_out is None):
        parser.error("--base-advice and --advice-out must be supplied together")
    hints = prepare(json.loads(args.records.read_text()))
    args.hints_out.write_bytes(hints)
    if args.base_advice:
        base = unpack_postcard_bytes(args.base_advice.read_bytes())
        payload = struct.pack("<Q", len(base)) + base + bytes((-len(base)) % 8) + hints
        args.advice_out.write_bytes(postcard_bytes(payload))
    print(json.dumps({"hint_bytes": len(hints)}))


if __name__ == "__main__":
    main()
