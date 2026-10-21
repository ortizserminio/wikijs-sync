"""Permite ejecutar la herramienta con: python -m wikijs_sync"""
import sys

from wikijs_sync.cli import main

if __name__ == "__main__":
    sys.exit(main())
