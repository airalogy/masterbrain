"""
Utility functions for printing.
"""


def print_with_border(*args, **kwargs):
    """
    A wrapper for the print function that adds a border around the printed content.
    """
    print()  # Add a newline before the border
    print("#" * 80)
    print(*args, **kwargs)
    print("#" * 80)
    print()  # Add a newline after the border