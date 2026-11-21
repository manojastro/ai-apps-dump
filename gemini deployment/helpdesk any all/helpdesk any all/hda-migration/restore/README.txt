The restore script itself lives in the git repository (it is not duplicated
into this archive, so it can't drift from the code it restores):

  scripts/cloud-migration/restore-new-vm.sh

On the new VM: clone the repo at commit 2ac28ed81bf19327c479622163a217f53c5f4f9c, then run that script and
point it at this backup archive.
