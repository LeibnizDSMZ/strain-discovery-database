# Configuration Guide

This document outlines the configuration options and security best practices for the data transformation pipeline. Proper configuration is essential for secure and successful execution.

## Overview

The pipeline relies on environment variables to manage credentials, database connections, and runtime options. These variables are loaded from a local configuration file during execution.

## Setup

1. **Locate the Template:**
   The project includes a template file named `package.env` containing all required variable keys.

2. **Create Your Configuration:**
   Copy the template to create your local configuration file.
   ```bash
   cp package.env .env
   ```

3. **Edit Configuration:**
   Open the `.env` file and populate the values.
   ```bash
   nano .env
   ```
   *Required fields typically include:*

      - `LPSN_USER` & `LPSN_PASSWORD`
      - `MONGO_SDD_PASSWORD`
      - `MONGO_PORT`

## Security Best Practices

> **⚠️ CRITICAL SECURITY WARNING**  
> The `.env` file contains sensitive credentials. **Never commit this file to version control.**

### 1. Secret Management
- **Local Development:** Storing secrets in `.env` is acceptable provided the file is not committed.
- **Production/Shared Environments:** Use dedicated secret management tools (e.g., Docker Secrets) instead of plain text files.

### 2. Shell History
Avoid passing sensitive credentials directly via command-line arguments, as these are often saved in shell history.

- ✅ **Recommended:** Use the `.env` file.
- ❌ **Discouraged:** `LPSN_PASSWORD=secret docker compose up --build`

### 3. File Permissions
Restrict access to the configuration file so only your user account can read it.
```bash
chmod 600 .env
```

## Troubleshooting

- **Variables Not Loading:** Ensure the file is named exactly `.env` and is located in the root directory where `docker compose` is executed.
- **Permission Denied:** Check file permissions using `ls -l .env` and adjust if necessary.
