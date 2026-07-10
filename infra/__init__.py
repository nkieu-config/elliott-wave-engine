"""Adapters that implement the ports declared by ``engine`` and ``analyst``.

Everything that talks to the outside world — yfinance, the parquet cache, Ollama —
lives here. Inner layers depend on the Protocols, never on this package.
"""
