#!/usr/bin/env python3
"""
Main entry point for the modular DPDA simulator.
This replaces the monolithic src/main.py with a cleaner, modular implementation
while maintaining backward compatibility.
"""

from cli_io.cli_interface import CLIInterface


def main():
    """Run the DPDA simulator in interactive mode."""
    cli = CLIInterface()
    cli.run_interactive_session()


if __name__ == "__main__":
    main()