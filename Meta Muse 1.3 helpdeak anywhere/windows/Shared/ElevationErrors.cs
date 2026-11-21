namespace HelpdeskAnywhere.Shared;

// Win32 error -> agent-facing message for elevation attempts (5.2b).
// Passwords never appear here: only the fact, result, and username are reported.
public static class ElevationErrors
{
    public const int Success = 0;
    public const int Cancelled = 1223;
    public const int LogonFailure = 1326;
    public const int BlankPasswordRestricted = 1327;
    public const int AccountDisabled = 1331;
    public const int LogonTypeNotGranted = 1385;
    public const int AccountLockedOut = 1909;

    public static string ToMessage(int code) => code switch
    {
        Success => "ok",
        Cancelled => "declined",
        LogonFailure => "logon failure: wrong username or password",
        BlankPasswordRestricted => "blank passwords are not allowed for this account",
        AccountDisabled => "account disabled",
        LogonTypeNotGranted => "account is not allowed interactive logon",
        AccountLockedOut => "account locked out",
        _ => $"windows error {code}",
    };

    public static bool IsCredentialProblem(int code) =>
        code is LogonFailure or BlankPasswordRestricted or AccountDisabled
            or LogonTypeNotGranted or AccountLockedOut;
}
