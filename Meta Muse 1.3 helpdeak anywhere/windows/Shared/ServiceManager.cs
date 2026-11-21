using System.Runtime.InteropServices;
using HelpdeskAnywhere.Shared.Interop;

namespace HelpdeskAnywhere.Shared;

// Install/start/stop/delete for HelpdeskAnywhereSvc via the SCM (5.2d, 5.7).
// The installer runs elevated; every failure carries the Win32 code so the
// agent sees actionable messages instead of raw numbers.
public static class ServiceManager
{
    public const string ServiceName = "HelpdeskAnywhereSvc";
    public const string DisplayName = "Helpdesk Anywhere Secure Desktop";
    public static string InstallDir =>
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "HelpdeskAnywhere");
    public const string ServiceExeName = "SecureDesktopService.exe";
    public const string HelperExeName = "DesktopHelper.exe";
    public static string ServiceExePath => Path.Combine(InstallDir, ServiceExeName);
    public static string HelperExePath => Path.Combine(InstallDir, HelperExeName);

    public static bool Exists()
    {
        IntPtr scm = OpenManager(ServiceInterop.SC_MANAGER_CREATE_SERVICE);
        if (scm == IntPtr.Zero) return false;
        try
        {
            IntPtr svc = ServiceInterop.OpenService(scm, ServiceName, ServiceInterop.SERVICE_QUERY_STATUS);
            if (svc == IntPtr.Zero) return false;
            _ = ServiceInterop.CloseServiceHandle(svc);
            return true;
        }
        finally
        {
            _ = ServiceInterop.CloseServiceHandle(scm);
        }
    }

    public static void Install(string binaryPath, string? arguments = null)
    {
        IntPtr scm = OpenManager(ServiceInterop.SC_MANAGER_CREATE_SERVICE);
        if (scm == IntPtr.Zero) ThrowWin32("open service manager");
        try
        {
            string imagePath = arguments is null ? $"\"{binaryPath}\"" : $"\"{binaryPath}\" {arguments}";
            IntPtr svc = ServiceInterop.CreateService(scm, ServiceName, DisplayName,
                ServiceInterop.SERVICE_ALL_ACCESS, ServiceInterop.SERVICE_WIN32_OWN_PROCESS,
                ServiceInterop.SERVICE_DEMAND_START, ServiceInterop.SERVICE_ERROR_NORMAL,
                imagePath, null, IntPtr.Zero, null, null, null);
            if (svc == IntPtr.Zero)
            {
                int code = Marshal.GetLastWin32Error();
                if (code != 1073) // ERROR_SERVICE_EXISTS: already installed, treat as success
                {
                    ThrowWin32("create service", code);
                }
                return;
            }
            _ = ServiceInterop.CloseServiceHandle(svc);
        }
        finally
        {
            _ = ServiceInterop.CloseServiceHandle(scm);
        }
    }

    public static void Start()
    {
        IntPtr scm = OpenManager(ServiceInterop.SC_MANAGER_CREATE_SERVICE);
        if (scm == IntPtr.Zero) ThrowWin32("open service manager");
        try
        {
            IntPtr svc = ServiceInterop.OpenService(scm, ServiceName,
                ServiceInterop.SERVICE_START | ServiceInterop.SERVICE_QUERY_STATUS);
            if (svc == IntPtr.Zero) ThrowWin32("open service");
            try
            {
                ServiceInterop.ServiceStatus status = default;
                if (ServiceInterop.QueryServiceStatus(svc, ref status) &&
                    status.DwCurrentState == ServiceInterop.SERVICE_RUNNING)
                {
                    return;
                }
                if (!ServiceInterop.StartService(svc, 0, null))
                {
                    int code = Marshal.GetLastWin32Error();
                    if (code != 1056) // ERROR_SERVICE_ALREADY_RUNNING
                    {
                        ThrowWin32("start service", code);
                    }
                }
            }
            finally
            {
                _ = ServiceInterop.CloseServiceHandle(svc);
            }
        }
        finally
        {
            _ = ServiceInterop.CloseServiceHandle(scm);
        }
    }

    public static void Stop()
    {
        IntPtr scm = OpenManager(ServiceInterop.SC_MANAGER_CREATE_SERVICE);
        if (scm == IntPtr.Zero) return;
        try
        {
            IntPtr svc = ServiceInterop.OpenService(scm, ServiceName,
                ServiceInterop.SERVICE_STOP | ServiceInterop.SERVICE_QUERY_STATUS);
            if (svc == IntPtr.Zero) return;
            try
            {
                ServiceInterop.ServiceStatus status = default;
                _ = ServiceInterop.ControlService(svc, ServiceInterop.SERVICE_CONTROL_STOP, ref status);
            }
            finally
            {
                _ = ServiceInterop.CloseServiceHandle(svc);
            }
        }
        finally
        {
            _ = ServiceInterop.CloseServiceHandle(scm);
        }
    }

    public static void Uninstall()
    {
        Stop();
        IntPtr scm = OpenManager(ServiceInterop.SC_MANAGER_CREATE_SERVICE);
        if (scm == IntPtr.Zero) return;
        try
        {
            IntPtr svc = ServiceInterop.OpenService(scm, ServiceName, ServiceInterop.DELETE);
            if (svc == IntPtr.Zero) return;
            try
            {
                _ = ServiceInterop.DeleteService(svc);
            }
            finally
            {
                _ = ServiceInterop.CloseServiceHandle(svc);
            }
        }
        finally
        {
            _ = ServiceInterop.CloseServiceHandle(scm);
        }
        try
        {
            if (Directory.Exists(InstallDir)) Directory.Delete(InstallDir, recursive: true);
        }
        catch (IOException)
        {
            // A helper binary may still be unloading; the directory is best-effort here
            // (the service watchdog retries, and reboot leaves nothing running).
        }
        catch (UnauthorizedAccessException)
        {
            // Same: best effort from a possibly non-elevated teardown path.
        }
    }

    private static IntPtr OpenManager(uint access)
    {
        return ServiceInterop.OpenSCManager(null, null, access);
    }

    private static void ThrowWin32(string action, int? code = null)
    {
        int c = code ?? Marshal.GetLastWin32Error();
        throw new InvalidOperationException($"Could not {action} (windows error {c}).");
    }
}
