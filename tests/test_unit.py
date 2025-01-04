import unittest
from apwgen import apwgen

class TestApwgenUnit(unittest.TestCase):

    def test_generate_syllable(self):
        """Test that generate_syllable returns a valid syllable of length 3."""
        syllable = apwgen.generate_syllable(apwgen.DEFAULT_VOWELS, apwgen.DEFAULT_CONSONANTS)
        self.assertEqual(len(syllable), 3)
        self.assertIn(syllable[0], apwgen.DEFAULT_CONSONANTS)
        self.assertIn(syllable[1], apwgen.DEFAULT_VOWELS)
        self.assertIn(syllable[2], apwgen.DEFAULT_CONSONANTS)

    def test_generate_word(self):
        """Test that generate_word generates a word with the correct number of syllables."""
        word = apwgen.generate_word(2, apwgen.DEFAULT_VOWELS, apwgen.DEFAULT_CONSONANTS)
        self.assertEqual(len(word), 6)  # Each syllable is 3 characters long

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

if __name__ == "__main__":
    unittest.main()
