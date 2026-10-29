from setuptools import setup, find_packages

setup(
    name="autopsy",
    version="1.0.0",
    description="AutoPSY: Anti-Forensic Detection & Evidence Integrity Framework for Software-Defined Vehicles",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    entry_points={"console_scripts": ["autopsy=autopsy.cli:main"]},
    author="Dr. Sapna VM, Prajwal Chowdary M, Prasad B Honnavalli",
)
