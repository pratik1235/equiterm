#!/usr/bin/env python3
"""
Entry point script for Equiterm application.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from equiterm.app import main

if __name__ == "__main__":
    main()
