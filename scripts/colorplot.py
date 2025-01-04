#!/usr/bin/env python
# encoding: utf-8
"""
Helper function to generate a heatmap (2D matrix) where:
    - X-axis represents the character position.
    - Y-axis represents unique characters (letters, digits, but no
       delimiters).
    - Color intensity indicates the frequency of each character at
       each position.
"""

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import apwgen

num_samples = 50000
options = apwgen.get_default_options()

# Generate passphrases
passphrases = [apwgen.generate_passphrase(options) for _ in range(num_samples)]

# Determine the maximum passphrase length
max_length = max(len(p) for p in passphrases)

# Identify all unique characters in the passphrases, exclude delimiters
unique_chars = sorted(set(''.join(passphrases)) - set(options.delimiters)) 

# Create a mapping from character to index
char_to_idx = {char: idx for idx, char in enumerate(unique_chars)}

# Initialize a frequency matrix
frequency_matrix = np.zeros((len(unique_chars), max_length))

# Populate the frequency matrix
for passphrase in passphrases:
    for position, char in enumerate(passphrase):
        if char in char_to_idx:
            frequency_matrix[char_to_idx[char], position] += 1

# Normalize the frequency matrix by the number of samples
frequency_matrix /= num_samples

# Set up the plot
plt.figure(figsize=(12, 8))

# Create the heatmap
sns.heatmap(frequency_matrix, cmap='viridis', cbar=True, xticklabels=range(max_length), yticklabels=unique_chars)

# Add labels and title
plt.xlabel('Character Position in Passphrase')
plt.ylabel('Character')
plt.title('Character Distribution in Generated Passphrases')

# Display the plot
plt.show()
