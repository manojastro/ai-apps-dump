# Frontend

The zero-build dashboard source is served by FastAPI from `backend/app/static`.
It deliberately uses semantic HTML, CSS, and small browser-native JavaScript so the POC has no Node toolchain or second runtime to operate. It calls only the versioned `/api/v1` API.
