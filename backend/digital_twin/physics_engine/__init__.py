"""Physics-based engine modeling utilities for Aerothon."""

from .physics_api import augment_with_physics

# Validation is available as a dedicated submodule to avoid importing
# matplotlib and other heavy dependencies during lightweight dataset exports.
