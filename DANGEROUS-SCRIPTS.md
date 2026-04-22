DANGEROUS SCRIPTS
=================

This repository contained scripts that can modify or wipe production data.
To avoid accidental data loss, the `seed.py` script has been disabled and
renamed to `seed.disabled.py`.

How to safely run destructive scripts
------------------------------------

1. Never run destructive scripts against production. Prefer to run them on a
   local or staging copy of the database.

2. Require two explicit confirmations to run:
   - set environment variable `ALLOW_SEED=1`
   - call the script with `--force --no-backup` only if you absolutely must
     skip backups (not recommended)

3. The repository provides a wrapper `scripts/run_seed_safe.py` which sets
   the required environment variable and auto-confirms. Use it only for
   developer-run seed tasks against non-production DBs.

4. Before running a seed against any MySQL-like production DB, create a
   full dump using `mysqldump` and store it in a safe location. Example:

   ```powershell
   mysqldump -h <host> -u <user> -p<password> <dbname> | gzip > backups/preseed-$(Get-Date -Format o).sql.gz
   ```

5. If you accidentally run a destructive script, immediately contact your
   DBA or hosting provider (Aiven) to restore from the latest backup.

Developer notes
---------------
- The authoritative seed content has been archived in the git history; to
  restore the seed script for any reason, consult the commit that created it.
- Consider implementing stricter CI and deployment checks to prevent
  production credentials from being present in development environments.
