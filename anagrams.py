#!/usr/bin/python3

"""Reduce an output to lines containing
at least X words with alt least Y characters each

"""

import sys


MIN_WORDS = 2
MIN_LENGTH = 6


def main():
    """Only print lines containing at least 2 words >= 5 characters long"""
    print(f"### Combinations with at least {MIN_WORDS} words each at least {MIN_LENGTH} characters long:")
    total = 0
    for line in sys.stdin:
        line = line.strip()
        long_words = set()
        for word in line.split():
            if len(word) >= MIN_LENGTH:
                long_words.add(word)
            #
        #
        if len(long_words) >= MIN_WORDS:
            total += 1
            print(line)
        #
    #
    print(f"### Total number found: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# vim: fileencoding=utf-8 sw=4 ts=4 sts=4 expandtab autoindent syntax=python:

