import unittest
import apwgen
import secrets
import collections
import string

class TestPassphraseEntropy(unittest.TestCase):

    def setUp(self):
        """Set up default options for passphrase generation."""
        self.options = apwgen.get_default_options()
        self.sample_size = 50000  # Number of passphrases to generate
        self.generated = {apwgen.generate_passphrase(self.options)
                          for _ in range(self.sample_size)}

    def test_passphrase_entropy(self):
        """Check if passphrases are unique to ensure good entropy."""
        self.assertEqual(len(self.generated), self.sample_size, "Passphrases are not unique enough!")

    def test_correct_digit_count(self):
        """Ensure each passphrase contains exactly the required number of digits."""
        for passphrase in self.generated:
            digit_count = sum(1 for c in passphrase if c in string.digits)
            self.assertEqual(digit_count, self.options.num_digits, f"Wrong number of digits in: {passphrase}")

    def test_correct_uppercase_count(self):
        """Ensure each passphrase contains exactly the required number of uppercase characters."""
        for passphrase in self.generated:
            uppercase_count = sum(1 for c in passphrase if c.isupper())
            self.assertEqual(uppercase_count, self.options.upper, f"Wrong number of uppercase letters in: {passphrase}")

    def test_correct_delimiter_usage(self):
        """Ensure delimiters are correctly placed between words."""
        for passphrase in self.generated:
            words = passphrase.split(self.options.delimiters)
            self.assertEqual(len(words), self.options.words, f"Delimiter error in: {passphrase}")

if __name__ == "__main__":
    unittest.main()
