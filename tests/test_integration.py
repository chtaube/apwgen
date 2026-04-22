import unittest
import subprocess


class TestApwgenCLI(unittest.TestCase):

    def test_help_message(self):
        """Test that running --help returns expected output."""
        result = subprocess.run(["python", "-m", "apwgen", "--help"], capture_output=True, text=True)
        self.assertIn("usage:", result.stdout)

    def test_version_output(self):
        """Test that --version outputs the correct information."""
        result = subprocess.run(["python", "-m", "apwgen", "--version"], capture_output=True, text=True)
        self.assertIn("Version", result.stdout)

    def test_passphrase_generation(self):
        """Test that passphrase generation returns a valid output."""
        result = subprocess.run(["python", "-m", "apwgen", "-w", "3", "-s", "2"], capture_output=True, text=True)
        passphrase = result.stdout.strip()
        self.assertGreater(len(passphrase), 0)

    def test_passphrase_contains_delimiter(self):
        """Test that a multi-word passphrase contains the expected delimiter."""
        result = subprocess.run(["python", "-m", "apwgen", "-w", "3", "-d", "-"], capture_output=True, text=True)
        self.assertIn("-", result.stdout.strip())

    def test_passphrase_word_count(self):
        """Test that the passphrase has the correct number of delimiter-separated words."""
        result = subprocess.run(["python", "-m", "apwgen", "-w", "3", "-d", "-", "-n0", "-u0"],
                                capture_output=True, text=True)
        words = result.stdout.strip().split("-")
        self.assertEqual(len(words), 3)

    def test_count_flag(self):
        """Test that -c generates the correct number of passphrases."""
        result = subprocess.run(["python", "-m", "apwgen", "-c", "5"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(len(lines), 5)

    def test_entropy_flag(self):
        """Test that -e prints an entropy estimate."""
        result = subprocess.run(["python", "-m", "apwgen", "-e"], capture_output=True, text=True)
        self.assertIn("Estimated entropy:", result.stdout)
        self.assertIn("bits", result.stdout)

    def test_entropy_increases_with_more_words(self):
        """Test that entropy grows when more words are requested."""
        def get_entropy(words):
            result = subprocess.run(["python", "-m", "apwgen", "-w", str(words), "-e"],
                                    capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "Estimated entropy:" in line:
                    return float(line.split()[2])
        self.assertGreater(get_entropy(4), get_entropy(3))

    def test_length_flag(self):
        """Test that -l enforces a minimum passphrase length."""
        result = subprocess.run(["python", "-m", "apwgen", "-l", "20"], capture_output=True, text=True)
        passphrase = result.stdout.strip()
        self.assertGreaterEqual(len(passphrase), 20)

    def test_length_reduces_entropy(self):
        """Test that --length reduces entropy compared to unconstrained generation."""
        def get_entropy(extra_args):
            result = subprocess.run(["python", "-m", "apwgen", "-e"] + extra_args,
                                    capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "Estimated entropy:" in line:
                    return float(line.split()[2])
        self.assertGreater(get_entropy([]), get_entropy(["-l", "22"]))

    def test_strict_flag_raises_on_impossible_request(self):
        """Test that --strict causes an error when digits can't be fully placed."""
        result = subprocess.run(
            ["python", "-m", "apwgen", "-w", "1", "-d", "", "-n", "5", "--strict"],
            capture_output=True, text=True)
        self.assertIn("Too many digits requested", result.stderr)

    def test_no_strict_does_not_crash_on_impossible_request(self):
        """Test that without --strict, over-requested digits are silently capped."""
        result = subprocess.run(
            ["python", "-m", "apwgen", "-w", "1", "-d", "", "-n", "5"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertGreater(len(result.stdout.strip()), 0)

    def test_no_digits(self):
        """Test that -n0 produces a passphrase with no digits."""
        result = subprocess.run(["python", "-m", "apwgen", "-n0", "-u0"], capture_output=True, text=True)
        passphrase = result.stdout.strip().replace("-", "")
        self.assertTrue(passphrase.isalpha())

    def test_custom_delimiter_pool(self):
        """Test that a multi-character delimiter pool uses only those characters."""
        result = subprocess.run(["python", "-m", "apwgen", "-w", "3", "-d", ":-/", "-c", "20", "-n0", "-u0"],
                                capture_output=True, text=True)
        for line in result.stdout.strip().splitlines():
            delimiters_used = [c for c in line if not c.isalpha()]
            self.assertTrue(all(c in ":-/" for c in delimiters_used))


if __name__ == "__main__":
    unittest.main()
