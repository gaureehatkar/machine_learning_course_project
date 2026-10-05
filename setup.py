from setuptools import setup, find_packages

setup(
    name="credit-decisioning",
    version="0.1.0",
    description="Policy-Constrained Credit Decisioning with Evidence-Quality Gating for Thin-File Gig/Platform Workers",
    packages=find_packages(exclude=["tests*", "notebooks*"]),
    python_requires=">=3.10",
)
