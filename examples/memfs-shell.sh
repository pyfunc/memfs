#!/bin/bash
# memfs-shell.sh

python -c "
from memfs.cli_with_shell import MemfsShell
MemfsShell().cmdloop()
"