# Judge-model policy

Every run persists provider, model, and judge implementation version. The default is `mock/mock-judge-v1/1.0.0`, a deterministic lexical judge needing no network or paid API. Unsupported provider/model combinations fail explicitly; they never fall back silently.

For a production semantic judge: pin provider/model/version/prompt/temperature, store those fields with the run, redact inputs, evaluate judge drift on a human-labeled calibration set, and require an explicit baseline migration when configuration changes. Do not directly compare runs produced by materially different judges.

