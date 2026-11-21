"""Seeded synthetic dataset generator (vendors, POs, GRNs, labeled invoices, contracts)."""

from invoiceflow.data.generator.build import DEFAULT_SEED, GENERATOR_VERSION, generate

__all__ = ["DEFAULT_SEED", "GENERATOR_VERSION", "generate"]
