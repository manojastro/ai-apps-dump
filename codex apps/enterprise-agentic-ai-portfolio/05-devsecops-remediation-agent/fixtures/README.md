# Inert security fixtures

Files under `inert/` end in `.txt`. They are examples for scanning demonstrations and
are never imported, executed, or copied into the application package. The simulator
keeps authoritative fixture text in `backend/app/simulator.py`; remediation accepts
only the exact known source hash and returns the exact reviewed fixed text.

All secrets and commands are nonfunctional examples. Do not rename these files to
`.py` or execute their contents.
