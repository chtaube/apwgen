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
import textwrap
from types import SimpleNamespace
from importlib.metadata import version, PackageNotFoundError


DEFAULT_VOWELS = 'aeiouy'
DEFAULT_CONSONANTS = 'bcdfghjkmnpqrstvwxz'
DEFAULT_NUMERICS = '0123456789'
DEFAULT_DELIMITERS = '-'

try:
    __version__ = version("apwgen")
except PackageNotFoundError:
    __version__ = None


def generate_syllable(vowels, consonants):
    '''
    Generate a syllable, consisting of a consonant, a vowel
    and another consonant.
    '''
    syllable = (secrets.choice(consonants)
                + secrets.choice(vowels)
                + secrets.choice(consonants))
    return syllable


def syllable_length():
    '''
    Return the length of a syllable.
    Currently, syllables have a fixed length of 3. So this function simply
    returns 3.
    You could calculate this with len(generate_syllable(...)) but this
    would unnecessarily drain the entropy pool.
    '''
    return 3


def generate_word(num_syllables, vowels, consonants):
    '''
    Generate a word, consisting of any number of syllabes as defined in
    num_syllables.
    '''
    if num_syllables <= 0:
        raise ValueError('Number of syllables must be positive.')
    return ''.join(generate_syllable(vowels, consonants)
                   for _ in range(num_syllables))


def generate_wordlist(num_words, num_syllables, vowels, consonants):
    '''
    Generate a list of words.
    '''
    if num_words <= 0:
        raise ValueError('Number of words must be positive.')
    wordlist = []
    for _ in range(num_words):
        wordlist.append(generate_word(num_syllables, vowels, consonants))
    return wordlist


def randomized_delimiter_join(words, delimiters):
    '''
    Join the words into a passphrase with random delimiters between each word.
    Raises ValueError when there is only word, so no delimiters can be added,
    unless no delimiters where requested.
    '''
    passphrase = words[0]
    if len(delimiters) > 0:
        if len(words) > 1:
            for word in words[1:]:
                passphrase += choose_delimiter(delimiters) + word
        else:
            raise ValueError('Not enough words to add delimiter between.')
    return passphrase


def choose_delimiter(delimiters):
    '''
    From the supplied list of delimiters, choose one randomly, or when only
    one delimiter is supplied, return this one.
    '''
    delimiters_length = len(delimiters)
    if delimiters_length == 1:
        return delimiters
    if delimiters_length > 1:
        return secrets.choice(delimiters)
    return ''


def get_possible_digit_positions(options):
    '''
    Returns a list of valid positions to add numbers. This is the
    character before or after a delimiter, or at the very last character
    position of the passphrase.
    '''
    if options.words <= 0:
        raise ValueError('Number of words must not be zero.')
    if options.syllables <= 0:
        raise ValueError('Number of syllables must not be zero.')
    # Using no delimiters is a valid option, currently.
    if len(options.delimiters) > 0:
        delimiter_length = 1
    else:
        delimiter_length = 0
    result = []
    for i in range(options.words):
        if i > 0:
            result.append(
                    i * delimiter_length
                    + i * options.syllables * syllable_length())
        result.append(
                i * delimiter_length
                + (i+1) * options.syllables * syllable_length()
                - 1)
    return result


def get_lc_positions(passphrase):
    '''
    Returns a list of lower case character positions.
    '''
    lc_positions = []
    i = 0
    for c in passphrase:
        if c.isalpha() and c.islower():
            lc_positions.append(i)
        i += 1
    return lc_positions


def replace_in_passphrase(passphrase, position, fn_modifier):
    '''
    Replace a single character in the passphrase. fn_modifier(c) is a lambda
    function which has the character to be replaced as a parameter.
    '''
    if len(passphrase) <= 0:
        raise ValueError(
                'In replace_in_password(), passphrase must not be empty.')
    if position < 0:
        raise ValueError(
                'In replace_in_password(), position must no be negative.')
    if position >= len(passphrase):
        raise ValueError(
                'In replace_in_password(), position must not exceed length '
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
    options.numbers = DEFAULT_NUMERICS
    options.delimiters = DEFAULT_DELIMITERS
    return options


def generate_passphrase(options):
    '''
    Generate a single passphrase, with all options applied
    (except options.count).
    '''
    passphrase = randomized_delimiter_join(
            generate_wordlist(
                options.words, options.syllables,
                options.vowels, options.consonants),
            options.delimiters)

    # add digits
    if options.allnums:
        maybe_digits = get_lc_positions(passphrase)
    else:
        maybe_digits = get_possible_digit_positions(options)

    if len(maybe_digits) < options.num_digits:
        raise ValueError('Too many digits requested (requested '
                         + f'{options.num_digits} of '
                         + f'{len(maybe_digits)} available).')
    if options.num_digits > len(maybe_digits):
        raise ValueError(f'Cannot insert {options.num_digits} digits, '
                         + f'only {len(maybe_digits)} positions available.')

    if options.num_digits > 0:
        for _ in range(options.num_digits):
            passphrase = replace_in_passphrase(
                    passphrase,
                    maybe_digits.pop(secrets.randbelow(len(maybe_digits))),
                    lambda _: secrets.choice(DEFAULT_NUMERICS))

    # add upper case
    lc_positions = get_lc_positions(passphrase)
    if len(lc_positions) < options.upper:
        raise ValueError('Too many upper case characters requested.')
    if options.upper > 0:
        for _ in range(options.upper):
            passphrase = replace_in_passphrase(
                    passphrase,
                    lc_positions.pop(secrets.randbelow(len(lc_positions))),
                    lambda c: c.upper())

    return passphrase


def emit_passphrases(options):
    '''
    Output any number of passphrases to the terminal.
    '''
    for i in range(options.count):
        try:
            print(generate_passphrase(options))
        except ValueError as e:
            print(f"Error generating passphrase {i+1}: {e}", file=sys.stderr)


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
        Note: Put the defaults in double quotes for presenting to the user.
        Windows command line accepts strings in double quotes only. Single
        quotes are used literally as parameter for an argument.
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
    if options.count <= 0:
        parser.error('The number of passphrases to generate (-c/--count) '
                     + 'must be greater than zero.')
    if options.num_digits < 0:
        parser.error(
                'The number of digits (-d/--numdigits) cannot be negative.')
    if options.upper < 0:
        parser.error(
                'The number of uppercase letters (-u/--upper) cannot '
                + 'be negative.')
    # check related parameters
    lc_avail = syllable_length() * options.syllables * options.words
    if options.allnums:
        if options.num_digits > (lc_avail - options.upper):
            parser.error(
                    'Sum of digits and upper case characters requested '
                    + 'exceeds length of passphrase '
                    + f'({options.num_digits} digits + {options.upper} '
                    + f'upper case > {lc_avail} available).')
    else:
        if options.num_digits > (2*options.words-1):
            parser.error(
                    'Too many digits requested. Maybe try adding --allnums?')
    if options.upper > (lc_avail - options.num_digits):
        parser.error(
                'Sum of digits and upper case characters requested exceeds '
                + f'length of passphrase ({options.num_digits} digits + '
                + f'{options.upper} upper case > {lc_avail} available).')


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
