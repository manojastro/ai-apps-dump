using System.Runtime.InteropServices;

namespace HelpdeskAnywhere.Shared.Interop;

// advapi32 Service Control Manager functions (repo convention: P/Invoke here).
internal static partial class ServiceInterop
{
    public const uint SC_MANAGER_CREATE_SERVICE = 0x0002;
    public const uint SERVICE_WIN32_OWN_PROCESS = 0x00000010;
    public const uint SERVICE_DEMAND_START = 0x00000003;
    public const uint SERVICE_ERROR_NORMAL = 0x00000001;
    public const uint SERVICE_QUERY_STATUS = 0x0004;
    public const uint SERVICE_START = 0x0010;
    public const uint SERVICE_STOP = 0x0020;
    public const uint DELETE = 0x00010000;
    public const uint SERVICE_ALL_ACCESS = 0x000F01FF;
    public const uint SERVICE_CONTROL_STOP = 0x00000001;
    public const uint SERVICE_STOPPED = 0x00000001;
    public const uint SERVICE_START_PENDING = 0x00000002;
    public const uint SERVICE_RUNNING = 0x00000004;

    [LibraryImport("advapi32.dll", EntryPoint = "OpenSCManagerW", StringMarshalling = StringMarshalling.Utf16, SetLastError = true)]
    public static partial IntPtr OpenSCManager(string? machineName, string? databaseName, uint access);

    [LibraryImport("advapi32.dll", EntryPoint = "CreateServiceW", StringMarshalling = StringMarshalling.Utf16, SetLastError = true)]
    public static partial IntPtr CreateService(IntPtr hSCManager, string serviceName, string displayName,
        uint access, uint serviceType, uint startType, uint errorControl,
        string binaryPath, string? loadOrderGroup, IntPtr tagId,
        string? dependencies, string? serviceAccount, string? password);

    [LibraryImport("advapi32.dll", EntryPoint = "OpenServiceW", StringMarshalling = StringMarshalling.Utf16, SetLastError = true)]
    public static partial IntPtr OpenService(IntPtr hSCManager, string serviceName, uint access);

    [LibraryImport("advapi32.dll", EntryPoint = "StartServiceW", StringMarshalling = StringMarshalling.Utf16, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool StartService(IntPtr hService, uint argc, string?[]? argv);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool ControlService(IntPtr hService, uint control, ref ServiceStatus status);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool DeleteService(IntPtr hService);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool CloseServiceHandle(IntPtr hSCObject);

    [LibraryImport("advapi32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static partial bool QueryServiceStatus(IntPtr hService, ref ServiceStatus status);

    [StructLayout(LayoutKind.Sequential)]
    internal struct ServiceStatus
    {
        public uint DwServiceType;
        public uint DwCurrentState;
        public uint DwControlsAccepted;
        public uint DwWin32ExitCode;
        public uint DwServiceSpecificExitCode;
        public uint DwCheckPoint;
        public uint DwWaitHint;
    }
}
