// Watches the input desktop and keeps a DesktopHelper on every non-Default
// desktop (Winlogon / Screen-saver). Runs as LocalSystem; --console runs the
// same loop as a plain process for diagnostics (the SYSTEM token dance only
// works under SCM, so --console can detect but not launch).
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.ServiceProcess;
using HelpdeskAnywhere.Shared;
using HelpdeskAnywhere.Shared.Interop;

namespace HelpdeskAnywhere.SecureDesktopService;

internal static class Program
{
    public static int Main(string[] args)
    {
        string pipe = Arg(args, "--pipe") ?? "";
        if (Arg(args, "--console") is not null || Environment.UserInteractive)
        {
            return Watcher.RunConsole(pipe);
        }
        ServiceBase.Run(new WatcherService(pipe));
        return 0;
    }

    internal static string? Arg(string[] args, string name)
    {
        for (int i = 0; i < args.Length; i++)
        {
            if (string.Equals(args[i], name, StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length)
            {
                return args[i + 1];
            }
        }
        return null;
    }
}

internal sealed class WatcherService(string pipeName) : ServiceBase
{
    private CancellationTokenSource? _cts;
    private Task? _loop;

    protected override void OnStart(string[] args)
    {
        ServiceName = ServiceManager.ServiceName;
        _cts = new CancellationTokenSource();
        _loop = Task.Run(() => Watcher.RunAsync(pipeName, _cts.Token));
    }

    protected override void OnStop()
    {
        try
        {
            _cts?.Cancel();
            _loop?.Wait(TimeSpan.FromSeconds(5));
        }
        catch
        {
            // stop path never throws
        }
        finally
        {
            _cts?.Dispose();
        }
    }
}

internal static class Watcher
{
    private const int PollMs = 200;
    private const int WatchdogSeconds = 60;

    internal static int RunConsole(string pipeName)
    {
        Console.WriteLine($"watcher console mode (pipe {(pipeName.Length > 0 ? "set" : "MISSING")})");
        try
        {
            RunAsync(pipeName, ConsoleCancelToken()).GetAwaiter().GetResult();
            return 0;
        }
        catch (OperationCanceledException)
        {
            return 0;
        }
    }

    private static CancellationToken ConsoleCancelToken()
    {
        CancellationTokenSource cts = new();
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };
        return cts.Token;
    }

    internal static async Task RunAsync(string pipeName, CancellationToken ct)
    {
        Dictionary<string, Process> helpers = new(StringComparer.Ordinal);
        string? current = null;
        DateTime lastPipeOk = DateTime.UtcNow;
        while (!ct.IsCancellationRequested)
        {
            try
            {
                string desktop = GetInputDesktopName();
                if (!string.Equals(desktop, current, StringComparison.Ordinal))
                {
                    Log($"desktop {current ?? "(start)"} -> {desktop}");
                    if (current is not null) StopHelper(helpers, current);
                    current = desktop;
                    if (!IsDefault(desktop))
                    {
                        StartHelper(helpers, desktop, pipeName);
                    }
                }
                // Watchdog: self-uninstall if the applet pipe stays unreachable.
                if (await PipeReachableAsync(pipeName, ct).ConfigureAwait(false))
                {
                    lastPipeOk = DateTime.UtcNow;
                }
                else if (DateTime.UtcNow - lastPipeOk > TimeSpan.FromSeconds(WatchdogSeconds))
                {
                    Log("pipe dead 60s, self-uninstalling");
                    foreach (string name in helpers.Keys.ToArray()) StopHelper(helpers, name);
                    try
                    {
                        ServiceManager.Uninstall();
                    }
                    catch
                    {
                        // best effort; SCM state may already be stopping
                    }
                    Environment.Exit(0);
                }
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                Log($"loop: {ex.GetType().Name}");
            }
            try
            {
                await Task.Delay(PollMs, ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                break;
            }
        }
        foreach (string name in helpers.Keys.ToArray()) StopHelper(helpers, name);
    }

    private static bool IsDefault(string desktop) =>
        string.Equals(desktop, "Default", StringComparison.OrdinalIgnoreCase);

    private static void StartHelper(Dictionary<string, Process> helpers, string desktop, string pipeName)
    {
        StopHelper(helpers, desktop);
        try
        {
            Process? child = LaunchInSession(
                ServiceManager.HelperExePath,
                $"--desktop \"{desktop}\" --pipe \"{pipeName}\"",
                $"WinSta0\\{desktop}");
            if (child is null)
            {
                Log($"launch skipped for {desktop} (no console session or token)");
                return;
            }
            helpers[desktop] = child;
            Log($"helper {desktop} pid {child.Id}");
        }
        catch (Exception ex)
        {
            Log($"launch {desktop} failed: {ex.GetType().Name}");
        }
    }

    private static void StopHelper(Dictionary<string, Process> helpers, string desktop)
    {
        if (!helpers.Remove(desktop, out Process? child)) return;
        try
        {
            if (!child.HasExited) child.Kill(entireProcessTree: true);
        }
        catch
        {
            // already gone
        }
        finally
        {
            child.Dispose();
        }
        Log($"helper {desktop} stopped");
    }

    private static string GetInputDesktopName()
    {
        IntPtr hDesk = DesktopInterop.OpenInputDesktop(0, false, DesktopInterop.GENERIC_ALL);
        if (hDesk == IntPtr.Zero) return "Default";
        try
        {
            uint needed = 0;
            _ = DesktopInterop.GetUserObjectInformation(hDesk, DesktopInterop.UOI_NAME, IntPtr.Zero, 0, out needed);
            if (needed == 0 || needed > 512) return "Default";
            IntPtr buf = Marshal.AllocHGlobal((int)needed);
            try
            {
                if (!DesktopInterop.GetUserObjectInformation(hDesk, DesktopInterop.UOI_NAME, buf, needed, out _))
                {
                    return "Default";
                }
                return Marshal.PtrToStringUni(buf) ?? "Default";
            }
            finally
            {
                Marshal.FreeHGlobal(buf);
            }
        }
        finally
        {
            _ = DesktopInterop.CloseDesktop(hDesk);
        }
    }

    // SYSTEM token -> duplicate -> move into the console session -> launch.
    private static Process? LaunchInSession(string exePath, string arguments, string desktop)
    {
        uint sessionId = SessionInterop.WTSGetActiveConsoleSessionId();
        if (sessionId == 0xFFFFFFFF) return null;
        if (!SessionInterop.OpenProcessToken(SessionInterop.GetCurrentProcess(),
                SessionInterop.TOKEN_DUPLICATE | SessionInterop.TOKEN_QUERY, out IntPtr selfToken))
        {
            return null;
        }
        try
        {
            SessionInterop.SecurityAttributes sa = new()
            {
                Length = Marshal.SizeOf<SessionInterop.SecurityAttributes>(),
            };
            if (!SessionInterop.DuplicateTokenEx(selfToken, SessionInterop.MAXIMUM_ALLOWED,
                    ref sa, SessionInterop.SecurityIdentification, SessionInterop.TokenPrimary, out IntPtr dup))
            {
                return null;
            }
            try
            {
                uint sid = sessionId;
                if (!SessionInterop.SetTokenInformation(dup, SessionInterop.TokenSessionId,
                        ref sid, (uint)Marshal.SizeOf<uint>()))
                {
                    return null;
                }
                IntPtr env = IntPtr.Zero;
                try
                {
                    _ = SessionInterop.CreateEnvironmentBlock(out env, dup, false);
                    LogonInterop.StartupInfo si = new()
                    {
                        Cb = Marshal.SizeOf<LogonInterop.StartupInfo>(),
                        Desktop = desktop,
                    };
                    SessionInterop.SecurityAttributes pa = new() { Length = Marshal.SizeOf<SessionInterop.SecurityAttributes>() };
                    SessionInterop.SecurityAttributes ta = new() { Length = Marshal.SizeOf<SessionInterop.SecurityAttributes>() };
                    string cmdLine = $"\"{exePath}\" {arguments}";
                    if (!SessionInterop.CreateProcessAsUser(dup, null, cmdLine, ref pa, ref ta,
                            false, SessionInterop.CREATE_UNICODE_ENVIRONMENT, env, null, ref si, out LogonInterop.ProcessInformation pi))
                    {
                        return null;
                    }
                    try
                    {
                        return Process.GetProcessById(pi.ProcessId);
                    }
                    catch (ArgumentException)
                    {
                        return null;
                    }
                    finally
                    {
                        _ = LogonInterop.CloseHandle(pi.HProcess);
                        _ = LogonInterop.CloseHandle(pi.HThread);
                    }
                }
                finally
                {
                    if (env != IntPtr.Zero) _ = SessionInterop.DestroyEnvironmentBlock(env);
                }
            }
            finally
            {
                _ = LogonInterop.CloseHandle(dup);
            }
        }
        finally
        {
            _ = LogonInterop.CloseHandle(selfToken);
        }
    }

    private static async Task<bool> PipeReachableAsync(string pipeName, CancellationToken ct)
    {
        if (pipeName.Length == 0) return true; // nothing to watch (console diagnostics)
        try
        {
            using PipeClient client = new(pipeName);
            await client.ConnectAsync(1000, ct).ConfigureAwait(false);
            return true;
        }
        catch
        {
            return false;
        }
    }

    private static void Log(string message)
    {
        try
        {
            string dir = ServiceManager.InstallDir;
            Directory.CreateDirectory(dir);
            File.AppendAllText(Path.Combine(dir, "service.log"),
                $"{DateTime.UtcNow:O} {message}{Environment.NewLine}");
        }
        catch
        {
            // logging never breaks the watcher
        }
    }
}
