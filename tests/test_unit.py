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
        """Test that generate_syllable returns a valid syllable of length 3."""
        syllable = apwgen.generate_syllable(apwgen.DEFAULT_VOWELS, apwgen.DEFAULT_CONSONANTS)
        self.assertEqual(len(syllable), apwgen.syllable_length())
        self.assertIn(syllable[0], apwgen.DEFAULT_CONSONANTS)
        self.assertIn(syllable[1], apwgen.DEFAULT_VOWELS)
        self.assertIn(syllable[2], apwgen.DEFAULT_CONSONANTS)

    def test_generate_word(self):
        """Test that generate_word generates a word with the correct number of syllables."""
        word = apwgen.generate_word(2, apwgen.DEFAULT_VOWELS, apwgen.DEFAULT_CONSONANTS)
        self.assertEqual(len(word), 2*apwgen.syllable_length())  # Each syllable is 3 characters long

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
        options = apwgen.get_default_options()
        self.assertEqual(
                apwgen.get_possible_digit_positions(options),
                [5, 7, 12, 14, 19])
        options.words = 4
        self.assertEqual(
                apwgen.get_possible_digit_positions(options),
                [5, 7, 12, 14, 19, 21, 26])
        options.words = 3
        options.delimiters = ''
        self.assertEqual(
                apwgen.get_possible_digit_positions(options),
                [5, 6, 11, 12, 17])
        options = apwgen.get_default_options()
        options.syllables = 3
        self.assertEqual(
                apwgen.get_possible_digit_positions(options),
                [8, 10, 18, 20, 28])


if __name__ == "__main__":
    unittest.main()
