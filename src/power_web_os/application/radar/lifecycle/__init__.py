"""Shared Radar run lifecycle records and application services.

Import concrete lifecycle modules directly so low-level record imports do not
eagerly initialize services that depend on application ports.
"""
