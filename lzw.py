#!/usr/bin/env python3

#
# LZW Compress/Decompress
#

import os
import io
import argparse

START_BITS = 9
CLEAR = 256
FIRST = 257

header_max_bits = 16
header_block_mode = True

stat_max_bits = START_BITS
stat_end_bits = START_BITS
stat_header_0 = 0
stat_header_1 = 0
stat_header_2 = 0

dictionary = {}
dict_index = FIRST
dict_size_max = pow(2, START_BITS)


def bits(sequence, n_bits, i_index, bits_index):
    if not isinstance(sequence, bytes) or n_bits == 0:
        raise ValueError()

    i_ix = i_index
    b_ix = bits_index
    part = ""

    while len(part) < n_bits and len(sequence) > i_ix:
        i = bin(sequence[i_ix])[2:]

        while len(i) % 8 > 0:
            i = "0" + i

        if b_ix > 0:
            i = i[: -1 * b_ix]

        part = i + part

        i_ix += 1
        b_ix = 0

    if len(part) < n_bits:
        if i_ix < len(sequence):
            raise ValueError(
                "%d < %d && %d < %d" % (len(part), n_bits, i_ix, len(sequence))
            )
        else:
            b = None
    else:
        b = part[-1 * n_bits :]

        r = len(part) - len(b)

        if r > 0:
            i_ix -= 1
            b_ix = 8 - r

    return (b, i_ix, b_ix)


def dict_init():
    global dictionary, dict_index, dict_size_max

    dictionary = {i: chr(i) for i in range(256)}
    dict_index = FIRST if header_block_mode else 256
    dict_size_max = pow(2, START_BITS)


def decompress(compressed):
    global dictionary, dict_index, dict_size_max, stat_max_bits, stat_end_bits, stat_header_0, stat_header_1, stat_header_2, header_max_bits, header_block_mode

    if not isinstance(compressed, bytes):
        raise ValueError("Bad input type: %s" % type(compressed))

    if len(compressed) < 3:
        raise ValueError("Bad input size: %d" % len(compressed))

    # First 3 bytes is the header
    stat_header_0 = compressed[0]
    stat_header_1 = compressed[1]
    stat_header_2 = compressed[2]

    header_max_bits = stat_header_2 & 0x1F

    if header_max_bits < START_BITS:
        header_max_bits = START_BITS

    header_block_mode = stat_header_2 & 0x80 > 0

    compressed = compressed[3:]

    i_size = len(compressed)

    print("Compressed blocks size: %d" % i_size)

    n_bits = START_BITS

    print("Start bit size: %d" % n_bits)

    result = io.StringIO()
    i_index = 0
    bits_index = 0
    w = ""
    n = 0
    init = True

    # Initialize dictionary
    dict_init()

    while i_index < i_size:
        b, i_index, bits_index = bits(compressed, n_bits, i_index, bits_index)

        if b is None:
            print("EOF. Breaking loop... (%d, %d)" % (i_index, i_size))
            break

        kw = int(b, 2)

        if kw == 0:
            print("%d: %s (%d, %s)" % (n, b, kw, w))
            raise ValueError("Corrupt input")

        if kw == CLEAR and header_block_mode:
            print("CLEAR CODE")
            raise ValueError()

            n_bits = START_BITS
            stat_end_bits = n_bits
            dict_init()
            init = True
        elif init:
            w = chr(kw)
            result.write(w)

            init = False
        else:
            if kw in dictionary:
                entry = dictionary[kw]
            elif kw == dict_index:
                entry = w + w[0]
            else:
                raise ValueError("%d: Bad keyword (%d)" % (n, kw))

            result.write(entry)

            if dict_index < dict_size_max:
                dictionary[dict_index] = w + entry[0]
                dict_index += 1

            w = entry

            if dict_index == dict_size_max and n_bits < header_max_bits:
                n_bits += 1
                dict_size_max = pow(2, n_bits)
                stat_end_bits = n_bits
                if n_bits > stat_max_bits:
                    stat_max_bits = n_bits
                print("New bit size: %d" % n_bits)

        n += 1

    return result.getvalue()


class Compress:
    def __init__(self, data):
        if not isinstance(data, str):
            raise ValueError()

        self.data = data
        self.n_bits = START_BITS
        self.reset_dict()

    def reset_dict(self):
        self.dictionary = {chr(i): i for i in range(256)}
        self.dict_index = FIRST if header_block_mode else 256
        self.dict_size_max = pow(2, START_BITS)

    def int_to_bin(self, i, n):
        b = bin(i)[2:]
        while len(b) < n:
            b = "0" + b
        return b

    def run(self):
        global stat_max_bits, stat_end_bits

        print("Start bit size: %d" % self.n_bits)

        o_bytes = bytearray()
        o_bytes.append(0x1F)
        o_bytes.append(0x9D)
        o_bytes.append(0x90)

        o_buffer = ""
        w = ""

        for c in self.data:
            wc = w + c
            if wc in self.dictionary:
                w = wc
            else:
                o_buffer = self.int_to_bin(self.dictionary[w], self.n_bits) + o_buffer

                if (
                    self.dict_index == self.dict_size_max
                    and self.n_bits < header_max_bits
                ):
                    self.n_bits += 1
                    self.dict_size_max = pow(2, self.n_bits)
                    stat_end_bits = self.n_bits
                    if self.n_bits > stat_max_bits:
                        stat_max_bits = self.n_bits
                    print("New bit size: %d" % self.n_bits)

                if self.dict_index < self.dict_size_max:
                    self.dictionary[wc] = self.dict_index
                    self.dict_index += 1

                w = c

                if len(o_buffer) > 8:
                    o_bytes.append(int(o_buffer[-8:], 2))
                    o_buffer = o_buffer[:-8]

        if w:
            o_buffer = self.int_to_bin(self.dictionary[w], self.n_bits) + o_buffer

        while len(o_buffer) > 0:
            if len(o_buffer) > 8:
                o_bytes.append(int(o_buffer[-8:], 2))
                o_buffer = o_buffer[:-8]
            else:
                o_bytes.append(int(o_buffer, 2))
                o_buffer = ""

        return bytes(o_bytes)


def decompress_file(i_file, o_file):
    with open(i_file, "rb") as f:
        data = f.read()

    decompressed = decompress(data)

    print("Input size: %d" % len(data))
    print("Header[0] = %s" % hex(stat_header_0))
    print("Header[1] = %s" % hex(stat_header_1))
    print("Header[2] = %s" % hex(stat_header_2))
    print("Max allowed bits = %d" % header_max_bits)
    print("Block mode = %s" % header_block_mode)
    print("Stream max bits: %d" % stat_max_bits)
    print("Stream end bits: %d" % stat_end_bits)
    print("Decompressed size: %d" % len(decompressed))

    with open(o_file, "w") as f:
        f.write(decompressed)


def compress_file(i_file, o_file):
    with open(i_file, "r") as f:
        data = f.read()

    compressed = Compress(data).run()

    print("Input size: %d" % len(data))
    print("Compressed size: %d" % len(compressed))
    print("Stream max bits: %d" % stat_max_bits)
    print("Stream end bits: %d" % stat_end_bits)

    with open(o_file, "wb") as f:
        f.write(compressed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LZW Compress/Decompress")
    parser.add_argument(
        "-d", "--decompress", help="Decompress mode", action="store_true"
    )
    parser.add_argument("-o", "--output", nargs=1, help="Output file")
    parser.add_argument("infile", metavar="INPUT", type=str, nargs=1, help="Input file")

    args = parser.parse_args()

    i_file = args.infile[0]

    if not os.path.isfile(i_file):
        raise Exception("File not found")

    o_file = args.output[0] if args.output else None

    if args.decompress:
        if not o_file:
            o_file = os.path.basename(i_file)
            if o_file.endswith(".Z"):
                o_file = o_file[:-2]
            else:
                o_file += ".out"

        decompress_file(i_file, o_file)
    else:
        if not o_file:
            o_file = "%s.Z" % os.path.basename(i_file)

        compress_file(i_file, o_file)
