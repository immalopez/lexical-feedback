from __future__ import annotations

from lexicalrichness import LexicalRichness


def get_lexical_richness(text):
    """
    Calculates the lexical richness of the text.
    """
    lex = LexicalRichness(text)
    return {
        "msttr": lex.msttr(segment_window=min(100, lex.words - 1)),
        "mattr": lex.mattr(window_size=min(100, lex.words - 1)),
        "ttr": lex.ttr,
        "rttr": lex.rttr,
        "cttr": lex.cttr,
        "mtld": lex.mtld(threshold=0.72),
        "hdd": lex.hdd(draws=min(42, lex.words)),
        "Herdan": lex.Herdan,
        "Summer": lex.Summer,
        "Dugast": lex.Dugast if lex.words != lex.terms else 0,
        "Maas": lex.Maas,
    }
