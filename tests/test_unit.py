#!/usr/bin/env python
# encoding: utf-8
"""
Unit test for apwgen. Still pretty basic, though.
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from apwgen import apwgen

class TestApwgenUnit(unittest.TestCase):

    def test_generate_syllable(self):
        """Test that generate_syllable returns a syllable matching its pattern's structure."""
        v, c = apwgen.DEFAULT_VOWELS, apwgen.DEFAULT_CONSONANTS
        for syllable_type, (nc, nv) in enumerate(apwgen.SYLLABLE_STRUCTURES):
            syllable = apwgen.generate_syllable(syllable_type, v, c)
            self.assertEqual(len(syllable), nc + nv)
            for ch in syllable:
                self.assertIn(ch, v + c)

    def test_generate_word(self):
        """Test that generate_word generates a word within the valid length range."""
        word = apwgen.generate_word(2, apwgen.DEFAULT_VOWELS, apwgen.DEFAULT_CONSONANTS)
        min_len = 2 * min(nc + nv for nc, nv in apwgen.SYLLABLE_STRUCTURES)
        max_len = 2 * max(nc + nv for nc, nv in apwgen.SYLLABLE_STRUCTURES)
        self.assertGreaterEqual(len(word), min_len)
        self.assertLessEqual(len(word), max_len)
        for ch in word:
            self.assertIn(ch, apwgen.DEFAULT_VOWELS + apwgen.DEFAULT_CONSONANTS)

    def test_generate_wordlist(self):
        """Test that generate_wordlist returns the correct number of words."""
        words = apwgen.generate_wordlist(5, 2, apwgen.DEFAULT_VOWELS, apwgen.DEFAULT_CONSONANTS)
        self.assertEqual(len(words), 5)

    def test_choose_delimiter(self):
        """Test delimiter selection."""
        delimiters = "-_/"
        delimiter = apwgen.choose_delimiter(delimiters)
        self.assertIn(delimiter, delimiters)

    def test_randomized_delimiter_join(self):
        """Test that words are properly joined by delimiters."""
        words = ["test", "word"]
        passphrase = apwgen.randomized_delimiter_join(words, "-_/")
        self.assertTrue(any(delimiter in passphrase for delimiter in "-_/"))

    def test_replace_in_passphrase(self):
        """Test replacing a character in the passphrase."""
        passphrase = "password"
        new_passphrase = apwgen.replace_in_passphrase(passphrase, 4, lambda _: "X")
        self.assertEqual(new_passphrase, "passXord")

    def test_validate_options(self):
        """Ensure validate_options correctly handles invalid inputs."""
        parser = apwgen.ApwgenArgumentParser()
        options = parser.parse_args(["-w", "0"])  # Invalid case
        with self.assertRaises(SystemExit):  # parser.error() calls sys.exit()
            apwgen.validate_options(parser, options)

    def test_get_lc_positions(self):
        challenges = [
                ("123abc", [3, 4, 5]),
                ("aBc-0dE", [0, 2, 5]),
                ("abcdef-ghijjk-lmnopq",
                 [0, 1, 2, 3, 4, 5, 7, 8, 9, 10,
                  11, 12, 14, 15, 16, 17, 18, 19]),
                ]
        for (c, result) in challenges:
            self.assertEqual(apwgen.get_lc_positions(c), result)

    def test_get_possible_digit_positions(self):
        # 3 words of 6 chars → passphrase "aaaaaa-bbbbbb-cccccc"
        self.assertEqual(
                apwgen.get_possible_digit_positions(["aaaaaa", "bbbbbb", "cccccc"]),
                [5, 7, 12, 14, 19])
        # 4 words of 6 chars
        self.assertEqual(
                apwgen.get_possible_digit_positions(["aaaaaa", "bbbbbb", "cccccc", "dddddd"]),
                [5, 7, 12, 14, 19, 21, 26])
        # 3 words of 9 chars (3 syllables × CVC)
        self.assertEqual(
                apwgen.get_possible_digit_positions(["aaaaaaaaa", "bbbbbbbbb", "ccccccccc"]),
                [8, 10, 18, 20, 28])
        # 3 words of 6 chars, no delimiter → passphrase "aaaaaabbbbbbcccccc"
        self.assertEqual(
                apwgen.get_possible_digit_positions(["aaaaaa", "bbbbbb", "cccccc"],
                                                    delimiter_len=0),
                [5, 6, 11, 12, 17])


if __name__ == "__main__":
    unittest.main()
