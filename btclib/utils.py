#!/usr/bin/env python3

# Copyright (C) 2017-2020 The btclib developers
#
# This file is part of btclib. It is subject to the license terms in the
# LICENSE file found in the top-level directory of this distribution.
#
# No part of btclib including this file, may be copied, modified, propagated,
# or distributed except according to the terms contained in the LICENSE file.

"""Assorted conversion utilities.

Most conversions from SEC 1 v.2 2.3 are included.

https://www.secg.org/sec1-v2.pdf
"""

import hashlib
from collections.abc import Iterable as IterableCollection
from io import BytesIO
from typing import Iterable, List, Optional, Union

from .alias import BinaryData, Integer, Octets, Printable, ScriptToken, String
from .exceptions import BTClibTypeError, BTClibValueError

# hexstr_from_bytes is not needed!!
# def hexstr_from_bytes(byte_str: bytes) -> str:
#    return byte_str.hex()


def sha256(octets: Octets) -> bytes:
    "Return the SHA256(*) of the input octet sequence."

    octets = bytes_from_octets(octets)
    return hashlib.sha256(octets).digest()


def hash160(octets: Octets) -> bytes:
    "Return the HASH160=RIPEMD160(SHA256) of the input octet sequence."

    t = sha256(octets)
    return hashlib.new("ripemd160", t).digest()


def hash256(octets: Octets) -> bytes:
    "Return the SHA256(SHA256(*)) of the input octet sequence."

    t = sha256(octets)
    return hashlib.sha256(t).digest()


NoneOneOrMoreInt = Optional[Union[int, Iterable[int]]]


def bytes_from_octets(octets: Octets, out_size: NoneOneOrMoreInt = None) -> bytes:
    """Return bytes from a hex-string, stripping leading/trailing spaces.

    If the input is not a string, then it goes untouched.
    Optionally, it also ensures required output size.
    """

    if isinstance(octets, str):  # hex string
        octets = bytes.fromhex(octets)

    if (
        out_size is None
        or isinstance(out_size, int)
        and len(octets) == out_size
        or isinstance(out_size, IterableCollection)
        and len(octets) in out_size
    ):
        return octets

    m = f"invalid size: {len(octets)} bytes instead of {out_size}"
    raise BTClibValueError(m)


def bytesio_from_binarydata(stream: BinaryData) -> BytesIO:
    """Return a BytesIO stream object from BinaryIO or Octets.

    If the input is not Octets (i.e. str or bytes),
    then it goes untouched.
    """

    if isinstance(stream, str):  # hex string
        stream = bytes_from_octets(stream)

    if isinstance(stream, bytes):
        stream = BytesIO(stream)

    return stream


def int_from_bits(octets: Octets, nlen: int) -> int:
    """Return the leftmost nlen bits.

    Take as input a sequence of blen bits and calculate a
    non-negative integer i that is less than 2^nlen according to
    SEC 1 v.2 section 4.1.3 (5).
    Note that an additional reduction modulo n would be required
    to ensure that 0 < i < n.

    int_from_bits is not the reverse of i.to_bytes, even
    for input sequences of length nlen: i.to_bytes will add some
    bits on the left, while int_from_bits will discard some bits on the
    right. i.to_bytes is the reverse of int_from_bits only when
    nlen is a multiple of 8 and bit sequences already have length nlen.
    See https://tools.ietf.org/html/rfc6979#section-2.3.5.
    """

    octets = bytes_from_octets(octets)
    i = int.from_bytes(octets, byteorder="big")

    blen = len(octets) * 8  # bits
    n = (blen - nlen) if blen >= nlen else 0
    return i >> n


def int_from_integer(i: Integer) -> int:
    """Return an int from many possible integer representations.

    Allowed integer representations are:

    * 3735928559
    * -3735928559
    * "0xdeadbeef"
    * "-0xdeadbeef"
    * "deadbeef"
    * b'\xde\xad\xbe\xef'

    The binary representation is not allowed because there is no way to
    discriminate it from a valid hex-string
    (e.g. "0b11011110101011011011111011101111").
    """

    if isinstance(i, int):
        return i
    if isinstance(i, str):
        i = i.strip().lower()
        if i.startswith("0x") or i.startswith("-0x"):
            return int(i, 16)
        i = bytes.fromhex(i)
    if not isinstance(i, bytes):
        raise BTClibTypeError("not an Integer=Union[int, str, bytes]")
    return int.from_bytes(i, "big")


def hex_string(i: Integer) -> str:
    """Return a hex-string from many positive integer representations.

    Negative integers are not allowed.

    The resulting hex-string has an even number of hex-digits and
    includes a space every four bytes (i.e. every eight hex-digits).
    """

    int_ = int_from_integer(i)
    if int_ < 0:
        raise BTClibValueError(f"negative integer: {int_}")
    a_str = hex(int_)[2:]
    if len(a_str) % 2 != 0:
        a_str = "0" + a_str

    indx = list(reversed(range(len(a_str), 0, -8)))
    lresult = [(a_str[max(0, i - 8) : i]) for i in indx]
    result = " ".join(lresult)
    return result.upper()


def ensure_is_power_of_two(n: int, var_name: str = None) -> None:
    # http://www.graphics.stanford.edu/~seander/bithacks.html
    if n & (n - 1) != 0:
        raise BTClibValueError(f"{var_name}: {n} (must be a power of two)")


def token_or_string_to_hex_string(val: Union[ScriptToken, String]) -> str:
    """Return a readable string from a ScriptToken or a String object.

    If val are bytes a hex string is returned.
    If val is an int his string representation is returned.
    """
    if isinstance(val, bytes):
        return val.hex()
    if isinstance(val, int):
        return str(val)
    return val


def token_or_string_to_printable(
    val: Union[List[ScriptToken], List[String]]
) -> List[Printable]:

    return [v.hex() if isinstance(v, bytes) else v for v in val]
