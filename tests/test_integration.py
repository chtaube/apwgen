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

if __name__ == "__main__":
    unittest.main()
