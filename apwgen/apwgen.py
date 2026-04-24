#!/usr/bin/env python
# encoding: utf-8
'''
apwgen.py
A phoneme-based passphrase generator inspired by the Apple Passwords app.
'''
import argparse
import secrets
import sys
import os
import math
import textwrap
from types import SimpleNamespace
from importlib.metadata import version, PackageNotFoundError


DEFAULT_VOWELS = 'aeiouy'
DEFAULT_CONSONANTS = 'bcdfghjkmnpqrstvwxz'
DEFAULT_NUMERICS = '0123456789'
DEFAULT_DELIMITERS = '-'

''' This pattern list is weighted, with the top entry
    having the highest probability.
'''
SYLLABLE_PATTERNS = [
        lambda v, c: c() + v() + c(),
        lambda v, c: c() + v() + v() + c(),
        lambda v, c: c() + v() + v(),
        lambda v, c: c() + v(),
        lambda v, c: v() + c(),
    ]

# (num_consonants, num_vowels) per pattern
SYLLABLE_STRUCTURES = (
        (2, 1),  # CVC
        (2, 2),  # CVVC
        (1, 2),  # CVV
        (1, 1),  # CV
        (1, 1),  # VC
    )
assert len(SYLLABLE_PATTERNS) == len(SYLLABLE_STRUCTURES), \
        "SYLLABLE_PATTERNS and SYLLABLE_STRUCTURES must have the same length"

try:
    __version__ = version("apwgen")
except PackageNotFoundError:
    __version__ = None


def _passphrase_length_pmf(options):
    '''
    Return the probability mass function of passphrase length (words + delimiters),
    before digit/uppercase substitutions (which don't change length).
    '''
    n = len(SYLLABLE_PATTERNS)
    probs = [(2 * (n - 1 - k) + 1) / (n * n) for k in range(n)]
    syl_pmf = {}
    for p, (nc_t, nv_t) in zip(probs, SYLLABLE_STRUCTURES):
        length = nc_t + nv_t
        syl_pmf[length] = syl_pmf.get(length, 0.0) + p

    pmf = {0: 1.0}
    for _ in range(options.words * options.syllables):
        new = {}
        for l1, p1 in pmf.items():
            for l2, p2 in syl_pmf.items():
                key = l1 + l2
                new[key] = new.get(key, 0.0) + p1 * p2
        pmf = new

    delimiter_len = (options.words - 1) if len(options.delimiters) > 0 else 0
    if delimiter_len > 0:
        pmf = {length + delimiter_len: p for length, p in pmf.items()}
    return pmf


def entropy_bits(options):
    '''
    Estimate the entropy in bits of a passphrase generated with the given options.
    Accounts for the non-uniform syllable type distribution of weighted_random()
    and the rejection sampling effect of --length.
    '''
    n = len(SYLLABLE_PATTERNS)
    # probability of each syllable type under weighted_random(n):
    # type k is picked when int(sqrt(r)) == n-1-k, which covers (2*(n-1-k)+1) values of r
    probs = [(2 * (n - 1 - k) + 1) / (n * n) for k in range(n)]
    nc = len(options.consonants)
    nv = len(options.vowels)

    h_type = -sum(p * math.log2(p) for p in probs)
    h_chars = sum(
            p * (nc_t * math.log2(nc) + nv_t * math.log2(nv))
            for p, (nc_t, nv_t) in zip(probs, SYLLABLE_STRUCTURES))
    h_words = options.words * options.syllables * (h_type + h_chars)

    if options.num_digits > 0:
        if options.allnums:
            avg_syl_len = sum(p * (nc_t + nv_t)
                              for p, (nc_t, nv_t) in zip(probs, SYLLABLE_STRUCTURES))
            num_pos = int(options.words * options.syllables * avg_syl_len)
        else:
            num_pos = 2 * options.words - 1
        h_digits = sum(
                math.log2(num_pos - i) + math.log2(len(options.numerics))
                for i in range(min(options.num_digits, num_pos)))
    else:
        h_digits = 0.0

    if options.upper > 0:
        avg_syl_len = sum(p * (nc_t + nv_t)
                          for p, (nc_t, nv_t) in zip(probs, SYLLABLE_STRUCTURES))
        avg_lc = options.words * options.syllables * avg_syl_len - options.num_digits
        h_upper = sum(math.log2(avg_lc - i)
                      for i in range(min(options.upper, int(avg_lc))))
    else:
        h_upper = 0.0

    h_delimiters = (options.words - 1) * math.log2(max(1, len(options.delimiters)))

    # --length applies rejection sampling: passphrases shorter than the threshold
    # are discarded. This conditions the distribution on len >= L, reducing entropy
    # by log2(P(len >= L)).
    if options.length is not None:
        pmf = _passphrase_length_pmf(options)
        p_accept = sum(p for length, p in pmf.items() if length >= options.length)
        h_length = math.log2(p_accept) if p_accept > 0 else -math.inf
    else:
        h_length = 0.0

    return h_words + h_digits + h_upper + h_delimiters + h_length


def weighted_random(n):
    '''
    Return a weighted random number in the range 0 and (n-1).
    '''
    r = secrets.randbelow(n * n)
    return (n - 1) - int(math.sqrt(r))


def generate_syllable(syllable_type, vowels, consonants):
    '''
    Generate a syllable
    '''
    v = lambda: secrets.choice(vowels)
    c = lambda: secrets.choice(consonants)
    return SYLLABLE_PATTERNS[syllable_type](v, c)


def generate_word(num_syllables, vowels, consonants):
    '''
    Generate a word, consisting of any number of syllabes as defined in
    num_syllables.
    '''
    if num_syllables <= 0:
        raise ValueError('Number of syllables must be positive.')

    return ''.join(generate_syllable(weighted_random(len(SYLLABLE_PATTERNS)),
                                     vowels, consonants)
                   for _ in range(num_syllables))


def generate_wordlist(num_words, num_syllables, vowels, consonants):
    '''
    Generate a list of words.
    '''
    if num_words <= 0:
        raise ValueError('Number of words must be positive.')
    return [generate_word(num_syllables, vowels, consonants)
            for _ in range(num_words)]


def randomized_delimiter_join(words, delimiters):
    '''
    Join the words into a passphrase with random delimiters between each word.
    Return the words when there are no delimiters. Or simple return the word
    when there is only one.
    '''
    if len(delimiters) == 0 or len(words) == 1:
        return ''.join(words)
    passphrase = words[0]
    for word in words[1:]:
        passphrase += secrets.choice(delimiters) + word
    return passphrase


def get_possible_digit_positions(wordlist, delimiter_len=1):
    if len(wordlist) <= 0:
        raise ValueError('Number of words must not be zero.')
    result = []
    total_length = 0
    for i in range(0, len(wordlist)):
        if i > 0:
            result.append(total_length)
        result.append(total_length + len(wordlist[i]) - 1)

        total_length += len(wordlist[i])
        if i < len(wordlist) - 1:
            total_length += delimiter_len
    return result


def get_lc_positions(passphrase):
    '''
    Returns a list of lower case character positions.
    '''
    lc_positions = []
    for i, c in enumerate(passphrase):
        if c.isalpha() and c.islower():
            lc_positions.append(i)
    return lc_positions


def replace_in_passphrase(passphrase, position, fn_modifier):
    '''
    Replace a single character in the passphrase. fn_modifier(c) is a lambda
    function which has the character to be replaced as a parameter.
    '''
    if len(passphrase) <= 0:
        raise ValueError(
                'In replace_in_passphrase(), passphrase must not be empty.')
    if position < 0:
        raise ValueError(
                'In replace_in_passphrase(), position must not be negative.')
    if position >= len(passphrase):
        raise ValueError(
                'In replace_in_passphrase(), position must not exceed length '
                + 'of passphrase.')

    passphrase_list = list(passphrase)
    passphrase_list[position] = fn_modifier(passphrase_list[position])
    return ''.join(passphrase_list)


def get_default_options():
    '''
    Helper function, primarily for the case when this is loaded
    as a Python module.
    '''
    options = SimpleNamespace()
    options.count = 1
    options.syllables = 2
    options.words = 3
    options.num_digits = 1
    options.allnums = False
    options.upper = 1
    options.vowels = DEFAULT_VOWELS
    options.consonants = DEFAULT_CONSONANTS
    options.numerics = DEFAULT_NUMERICS
    options.delimiters = DEFAULT_DELIMITERS
    options.strict = False
    options.length = None
    options.entropy = False
    return options


def generate_passphrase(options):
    '''
    Generate a single passphrase, with all options applied
    (except options.count).
    '''
    n = 0
    while True:
        n += 1
        wordlist = generate_wordlist(
                options.words, options.syllables,
                options.vowels, options.consonants)

        passphrase = randomized_delimiter_join(wordlist, options.delimiters)
        if options.length is None:
            break
        if len(passphrase) >= options.length:
            break
        if n >= 1000:
            raise ValueError('Couldn\'t generate passphrase with specified minimum length.')

    # add digits
    if options.allnums:
        maybe_digits = get_lc_positions(passphrase)
    else:
        maybe_digits = get_possible_digit_positions(wordlist,
                                                    1 if options.delimiters else 0)

    if options.strict and len(maybe_digits) < options.num_digits:
        raise ValueError('Too many digits requested ('
                         + f'{options.num_digits} / '
                         + f'{len(maybe_digits)}).')
    for _ in range(min(options.num_digits, len(maybe_digits))):
        passphrase = replace_in_passphrase(
                passphrase,
                maybe_digits.pop(secrets.randbelow(len(maybe_digits))),
                lambda _: secrets.choice(options.numerics))

    # add upper case
    lc_positions = get_lc_positions(passphrase)
    if options.strict and len(lc_positions) < options.upper:
        raise ValueError('Too many upper case characters requested.')
    for _ in range(min(options.upper, len(lc_positions))):
        passphrase = replace_in_passphrase(
                passphrase,
                lc_positions.pop(secrets.randbelow(len(lc_positions))),
                lambda c: c.upper())

    return passphrase


def emit_passphrases(options):
    '''
    Output any number of passphrases to the terminal.
    '''
    err = 0
    for i in range(options.count):
        try:
            print(generate_passphrase(options))
        except ValueError as e:
            if options.count == 1:
                print(f" {e}", file=sys.stderr)
                break
            else:
                err += 1
                last_err = e
    if err > 0:
        print(f" Passphrase generation failed for {err} passphrases. \n"
              + " Check your options and retry. Last error was: \n"
              + f"  {last_err}", file=sys.stderr)
    if options.entropy:
        bits = entropy_bits(options)
        if math.isinf(bits):
            print("Estimated entropy: n/a (minimum length is unreachable)")
        else:
            print(f"Estimated entropy: {bits:.1f} bits")


class ApwgenArgumentParser(argparse.ArgumentParser):
    '''
    Command line argument parser for this program.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._add_arguments()

    def _add_arguments(self):
        '''
        Arguments needed for this program.
        Note: Within the help text, always put the defaults in double quotes.
        Windows command line accepts strings in double quotes only.
        Single quotes are used literally as parameter for an argument.
        '''
        self.add_argument(
                '--version', action=ApwgenVersion, nargs=0,
                help='Show version and author information.')
        self.add_argument(
                '-w', '--words',
                type=int, default=3,
                help='Specify the number of words to add.')
        self.add_argument(
                '-s', '--syllables',
                type=int, default=2,
                help='Specify the number of syllables a single word '
                + 'should contain.')
        self.add_argument(
                '-c', '--count',
                type=int, default=1,
                help='Number of passphrases to generate. One per line.')
        self.add_argument(
                '-u', '--upper',
                type=int, default=1,
                help='Number of upper case characters to include.')
        self.add_argument(
                '-n', '--numdigits', dest='num_digits',
                type=int, default=1,
                help='Number of digits to include in passphrase.')
        self.add_argument(
                '-l', '--length',
                type=int, default=None,
                help='Ensure a minimum password length after all modifiers were applied.')
        self.add_argument(
                '-a', '--allnums',
                action='store_true',
                help='Allow digits to be placed on a any position. Otherwise '
                + 'they will be allowed only before or after a delimiter and '
                + 'on the last position.')
        self.add_argument(
                '-d', '--delimiters', type=str, default=DEFAULT_DELIMITERS,
                help='Delimiter(s) to put between words. '
                + f'Default: "{DEFAULT_DELIMITERS}"')
        self.add_argument(
                '--vowels', type=str, default=DEFAULT_VOWELS,
                help='Specifies the vowel pool for syllables. '
                + f'Default: "{DEFAULT_VOWELS}"')
        self.add_argument(
                '--consonants', type=str, default=DEFAULT_CONSONANTS,
                help='Specifies the consonant pool for syllables. '
                + f'Default: "{DEFAULT_CONSONANTS}"')
        self.add_argument(
                '--numerics', type=str, default=DEFAULT_NUMERICS,
                help='Specify the digit pool. '
                + f'Default: "{DEFAULT_NUMERICS}"')
        self.add_argument(
                '--strict',
                action='store_true',
                help='Ensure all modifiers (upper case, digits) could be applied. ')
        self.add_argument(
                '-e', '--entropy',
                action='store_true',
                help='Show estimated entropy in bits after generating passphrases.')

class ApwgenVersion(argparse.Action):
    '''
    Output version and author information (with --version)
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        print(textwrap.dedent(f'''
            {parser.prog} Version {__version__}
            A phoneme-based passphrase generator inspired by the Apple Passwords app.

            Licensed under the European Union Public License Version 1.2 (EUPL-v1.2)
            https://github.com/chtaube/apwgen
        ''').strip())
        parser.exit()


def validate_options(parser, options):
    '''
    Some sanity checks on user supplied input.
    '''
    # basic boundary checks
    if options.words <= 0:
        parser.error(
                'The number of words (-w/--words) must be greater than zero.')
    if options.syllables <= 0:
        parser.error(
                'The number of syllables per word (-s/--syllables) must be '
                + 'greater than zero.')
    if options.count < 0:
        parser.error('The number of passphrases to generate (-c/--count) '
                     + 'must be greater than zero.')
    if options.num_digits < 0:
        parser.error(
                'The number of digits (-n/--numdigits) cannot be negative.')
    if options.upper < 0:
        parser.error(
                'The number of uppercase letters (-u/--upper) cannot '
                + 'be negative.')


def main(argv=None):
    '''
    Main code for this program
    '''
    if argv is None:
        argv = sys.argv

    exit_status = 0

    try:
        program_name = os.path.basename(argv[0])
        parser = ApwgenArgumentParser(prog=program_name)

        options = parser.parse_args(argv[1:])
        validate_options(parser, options)

        emit_passphrases(options)

    except SystemExit as exc:
        exit_status = exc.code

    return exit_status


if __name__ == '__main__':
    exit_status = main(sys.argv)
    sys.exit(exit_status)
