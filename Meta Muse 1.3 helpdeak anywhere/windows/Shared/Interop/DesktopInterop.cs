using System.Runtime.InteropServices;

namespace HelpdeskAnywhere.Shared.Interop;

// Token/session functions for launching the helper as SYSTEM inside the
// interactive session (5.3), plus desktop functions (5.4) and SendSAS (4.3).
internal static partial class DesktopInterop
{
    public const int UOI_NAME = 2;
    public const uint GENERIC_ALL = 0x10000000;

    [LibraryImport("user32.dll", SetLastError = true)]
    public static partial IntPtr OpenInputDesktop(uint flags, [MarshalAs(UnmanagedType.Bool)] bool inherit, uint access);

    [LibraryImport("user32.dll", EntryPoint = "GetUserObjectInformationW", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool GetUserObjectInformation(IntPtr hObj, int nIndex,
        IntPtr pvInfo, uint nLength, out uint needed);

    [LibraryImport("user32.dll", EntryPoint = "OpenDesktopW", StringMarshalling = StringMarshalling.Utf16, SetLastError = true)]
    public static partial IntPtr OpenDesktop(string desktop, uint flags,
        [MarshalAs(UnmanagedType.Bool)] bool inherit, uint access);

    [LibraryImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool SetThreadDesktop(IntPtr hDesktop);

    [LibraryImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool CloseDesktop(IntPtr hDesktop);

    // Software Secure Attention Sequence (Ctrl+Alt+Del) from the elevated
    // helper. Only meaningful on Phase 5 paths; disabled in the console prior.
    [LibraryImport("sas.dll", SetLastError = true)]
    public static partial void SendSAS([MarshalAs(UnmanagedType.Bool)] bool asUser);
}

internal static partial class SessionInterop
{
    public const uint TOKEN_DUPLICATE = 0x0002;
    public const uint TOKEN_QUERY = 0x0008;
    public const uint MAXIMUM_ALLOWED = 0x02000000;
    public const int SecurityIdentification = 1;
    public const int TokenPrimary = 1;
    public const int TokenSessionId = 12;
    public const uint CREATE_UNICODE_ENVIRONMENT = 0x00000400;
    public const uint CREATE_NO_WINDOW = 0x08000000;

    [LibraryImport("wtsapi32.dll", SetLastError = true)]
    public static partial uint WTSGetActiveConsoleSessionId();

    [LibraryImport("kernel32.dll", SetLastError = true)]
    public static partial IntPtr GetCurrentProcess();

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool OpenProcessToken(IntPtr processHandle, uint access, out IntPtr tokenHandle);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool DuplicateTokenEx(IntPtr existingToken, uint access,
        ref SecurityAttributes attributes, int impersonationLevel, int tokenType, out IntPtr newToken);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool SetTokenInformation(IntPtr token, int infoClass,
        ref uint info, uint infoLength);

    [LibraryImport("userenv.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool CreateEnvironmentBlock(out IntPtr environment, IntPtr token, [MarshalAs(UnmanagedType.Bool)] bool inherit);

    [LibraryImport("userenv.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool DestroyEnvironmentBlock(IntPtr environment);

    // Same struct-marshaling note as LogonInterop.CreateProcessWithLogon.
    [DllImport("advapi32.dll", EntryPoint = "CreateProcessAsUserW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CreateProcessAsUser(IntPtr token, string? appName, string commandLine,
        ref SecurityAttributes processAttributes, ref SecurityAttributes threadAttributes,
        [MarshalAs(UnmanagedType.Bool)] bool inheritHandles, uint creationFlags, IntPtr environment,
        string? currentDirectory, ref LogonInterop.StartupInfo startupInfo,
        out LogonInterop.ProcessInformation processInformation);

    [StructLayout(LayoutKind.Sequential)]
    internal struct SecurityAttributes
    {
        public int Length;
        public IntPtr SecurityDescriptor;
        public int InheritHandle;
    }
}
