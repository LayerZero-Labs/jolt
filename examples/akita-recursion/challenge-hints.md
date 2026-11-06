# Authenticated challenge advice

Build the external guest with `guest,checked-challenge-advice` to enable the
checked advice path. Without that feature it accepts ordinary outer advice.

With the feature selected, it accepts a Postcard byte string containing an eight-byte
little-endian outer-advice length, the original outer-advice bytes, zero padding
to an eight-byte boundary, and an `AKITAH02` hint frame. The hint frame contains
an eight-byte quartet-tape length, quartet words, and position words.

Each quartet code, subset rank, sign and operator-norm acceptance decision is
checked against transcript-derived values inside the guest. Unused, malformed
or reordered hint words reject. Advice is untrusted and does not replace setup
material bound to the committed verifier image.

Prepare advice from ordered records with:

```sh
python3 examples/akita-recursion/prepare-challenge-hints.py records.json \
  --hints-out hints.bin --base-advice outer-advice.bin --advice-out advice.bin
```

`outer-advice.bin` is the original Postcard byte-string advice. `records.json`
contains `quartet_messages`, an ordered array of hexadecimal D64/31/10 transcript
messages routed through quartet decoding, and `position_ranks`, an ordered array
of objects with `n`, `pm1`, `pm2`, `rank1` and `rank2`. The latter includes every
rank-valid candidate inspected by the ordinary decoder, including candidates
rejected by the operator-norm predicate. The second subset rank is in the
complement domain of size `n-pm1`. The caller obtaining these records from a
native replay must preserve draw and candidate order. The preparation utility
is untrusted; incorrect records cause guest verification to reject.

The dependency pin includes the individually reviewed portable verifier
optimizations. The recorded full-stack result was 397,276,220 guest cycles with
field and NTT inlines disabled; ten committed proofs were generated and verified.
That measurement predates these publication ports and is not a benchmark of
any individual PR branch. Rebuild and rerun before asserting that exact count
for this fork.
