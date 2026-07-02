#!/bin/zsh
set -euo pipefail

cd /Users/kojinn/2nd-Brain-master
/usr/bin/python3 02_経営/帳簿/scripts/monthly_accounting_recheck.py "$@"
