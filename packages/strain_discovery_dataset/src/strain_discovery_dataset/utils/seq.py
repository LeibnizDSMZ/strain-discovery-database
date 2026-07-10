# SPDX-FileCopyrightText: 2026 Leibniz Institute DSMZ-German Collection of Microorganisms and Cell Cultures GmbH
#
# SPDX-License-Identifier: MIT

from typing import Any
import re


_CLEAN = re.compile(r"^([^.]+)(\.\d+)?$")


def get_seq_acc(seq_acc: str, /) -> str:
    match = _CLEAN.search(seq_acc)
    if match is None:
        raise ValueError(f"Invalid sequence accession: {seq_acc}")
    return match.group(1)


def get_seq_length(length: Any) -> None | str:
    if length is None:
        return None
    return str(length)
