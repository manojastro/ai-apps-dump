using System.Runtime.InteropServices;

namespace HelpdeskAnywhere.Shared.Interop;

// Logon + process-creation functions for credential-mode elevation (5.2b).
// Passwords arrive as char[] and are zeroed by the caller after the single use.
internal static partial class LogonInterop
{
    public const uint LOGON_WITH_PROFILE = 0x00000001;
    public const uint CREATE_UNICODE_ENVIRONMENT = 0x00000400;
    public const uint CREATE_NO_WINDOW = 0x08000000;
    public const int LOGON32_LOGON_INTERACTIVE = 2;
    public const int LOGON32_PROVIDER_DEFAULT = 0;

    // CreateProcessWithLogonW takes a string-bearing STARTUPINFO struct, which
    // source-generated P/Invoke cannot marshal — classic DllImport here.
    [DllImport("advapi32.dll", EntryPoint = "CreateProcessWithLogonW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CreateProcessWithLogon(string username, string? domain, string password,
        uint logonFlags, string? appName, string commandLine, uint creationFlags,
        IntPtr environment, string? currentDirectory, ref StartupInfo startupInfo,
        out ProcessInformation processInformation);

    [LibraryImport("advapi32.dll", EntryPoint = "LogonUserW", StringMarshalling = StringMarshalling.Utf16, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool LogonUser(string username, string? domain, string password,
        int logonType, int logonProvider, out IntPtr token);

    [LibraryImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool CloseHandle(IntPtr handle);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    internal struct StartupInfo
    {
        public int Cb;
        public string? Reserved;
        public string? Desktop;
        public string? Title;
        public int X;
        public int Y;
        public int XSize;
        public int YSize;
        public int XCountChars;
        public int YCountChars;
        public int FillAttribute;
        public int Flags;
        public short ShowWindow;
        public short Reserved2;
        public IntPtr Reserved3;
        public IntPtr StdInput;
        public IntPtr StdOutput;
        public IntPtr StdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    internal struct ProcessInformation
    {
        public IntPtr HProcess;
        public IntPtr HThread;
        public int ProcessId;
        public int ThreadId;
    }
}
