"""Turkish-aware case handling. ``str.lower``/``str.upper`` get İ/ı wrong."""

from __future__ import annotations

import unicodedata

_ASCII_FOLD = str.maketrans("çğıöşüâîû", "cgiosuaiu")
_PUNCT = str.maketrans("", "", ".,;:'’`\"()")


def lower(text: str) -> str:
    """``"İSTANBUL"`` → ``"istanbul"``, ``"ISPARTA"`` → ``"ısparta"``."""
    s = text.replace("İ", "i").replace("I", "ı").lower()
    return unicodedata.normalize("NFC", s).replace("̇", "")


def upper(text: str) -> str:
    """``"istanbul"`` → ``"İSTANBUL"``, ``"ılgaz"`` → ``"ILGAZ"``."""
    return text.replace("i", "İ").replace("ı", "I").upper()


def fold(text: str) -> str:
    """Comparison key: lowercase, plain ASCII letters, no punctuation.

    >>> fold("KÂĞITHANE") == fold("Kagithane") == fold("kâğıthane")
    True
    """
    s = lower(text).translate(_ASCII_FOLD).translate(_PUNCT)
    return " ".join(s.split())


def title(text: str) -> str:
    """Title-case words that are all upper or all lower; leave mixed case alone.

    >>> title("ATATÜRK MAH")
    'Atatürk Mah'
    >>> title("kızılay")
    'Kızılay'
    >>> title("McDonald")
    'McDonald'
    """
    out = []
    for word in text.split(" "):
        letters = [c for c in word if c.isalpha()]
        if letters and (word == upper(word) or word == lower(word)):
            word = upper(word[:1]) + lower(word[1:])
        out.append(word)
    return " ".join(out)
