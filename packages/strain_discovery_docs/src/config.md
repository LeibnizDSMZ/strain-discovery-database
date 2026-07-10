# Configuration Guide

This document explains the configuration options for the data transformation pipeline.

## Main Config File

- Located at `.env`.
- Must be created based on `package.env` (a copy is sufficient).
- Contains credentials, MongoDB connection info, and pipeline options.

## Security

- It is recommended to not add passwords to `.env` file.
- Use environment variables or secret management for sensitive data.
- It is recommended to disable history for the current shell.
