// One-time elevation bootstrap (5.2). Two modes converge on --install-service:
// an elevated copy of this exe stages the service binaries, creates + starts
// HelpdeskAnywhereSvc, and reports back over the session pipe.
//
// Credential hygiene (5.2c): the password lives only in the unelevated parent
// as char[], is used for exactly one CreateProcessWithLogonW call, and is
// zeroed in a finally. The elevated child never receives it. Nothing secret
// is written to any log, pipe, or exception message.
using System.ComponentModel;
using System.Diagnostics;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using HelpdeskAnywhere.Shared;
using HelpdeskAnywhere.Shared.Interop;

namespace HelpdeskAnywhere.Applet.Elevation;

internal static class Installer
{
    // Elevated child entry point. Returns a process exit code, never throws.
    public static int RunInstallService(string pipeName)
    {
        try
        {
            StageBinaries();
            ServiceManager.Install(ServiceManager.ServiceExePath, $"--pipe \"{pipeName}\"");
            ServiceManager.Start();
            Report(pipeName, true, "ok");
            return 0;
        }
        catch (Exception ex)
        {
            int code = ex is Win32Exception w32 ? w32.NativeErrorCode : Marshal.GetLastWin32Error();
            Report(pipeName, false, ElevationErrors.ToMessage(code));
            return 3;
        }
    }

    public static int RunUninstallService()
    {
        try
        {
            ServiceManager.Uninstall();
            return 0;
        }
        catch
        {
            return 1;
        }
    }

    // TEST-ONLY error-mapping probe (no session, no TLS guard): attempts a
    // logon with a caller-supplied throwaway password from HDA_TEST_PASSWORD
    // and prints the mapped message. Never prints the password.
    public static int RunTestLogon()
    {
        string domain = Environment.GetEnvironmentVariable("HDA_TEST_DOMAIN") ?? ".";
        string username = Environment.GetEnvironmentVariable("HDA_TEST_USER") ?? "nosuchuser";
        string passwordEnv = Environment.GetEnvironmentVariable("HDA_TEST_PASSWORD") ?? "";
        char[] password = passwordEnv.ToCharArray();
        try
        {
            LaunchWithCredentials(domain, username, password, $"hda-testlogon-{Guid.NewGuid():N}");
            Console.WriteLine("unexpected success");
            return 1;
        }
        catch (Win32Exception ex)
        {
            Console.WriteLine(ElevationErrors.ToMessage(ex.NativeErrorCode));
            return 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"other: {ex.GetType().Name}");
            return 1;
        }
        finally
        {
            Array.Clear(password, 0, password.Length);
        }
    }

    private static void StageBinaries()
    {
        Directory.CreateDirectory(ServiceManager.InstallDir);
        CopyPayload(ServiceManager.ServiceExeName, ServiceManager.ServiceExePath);
        CopyPayload(ServiceManager.HelperExeName, ServiceManager.HelperExePath);
    }

    private static void CopyPayload(string fileName, string destPath)
    {
        // 1. Side-by-side (local builds, tests).
        string? ownDir = Path.GetDirectoryName(Environment.ProcessPath);
        if (ownDir is not null)
        {
            string side = Path.Combine(ownDir, fileName);
            if (File.Exists(side))
            {
                File.Copy(side, destPath, overwrite: true);
                return;
            }
        }
        // 2. Embedded in the single-file download (production path).
        string resource = $"Applet.Resources.{fileName}";
        using Stream? stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(resource);
        if (stream is null)
        {
            throw new InvalidOperationException($"Service payload {fileName} not found.");
        }
        using FileStream outFile = File.Create(destPath);
        stream.CopyTo(outFile);
    }

    private static void Report(string pipeName, bool ok, string error)
    {
        try
        {
            using PipeClient pipe = new(pipeName);
            // Generous connect: the instance may be held until a handshake drop.
            pipe.ConnectAsync(30000, CancellationToken.None).GetAwaiter().GetResult();
            string json = JsonSerializer.Serialize(new { t = "install.result", ok, error });
            pipe.WriteFrameAsync(Encoding.UTF8.GetBytes(json), CancellationToken.None).GetAwaiter().GetResult();
        }
        catch
        {
            // The parent times out and reports failure itself.
        }
    }

    // Mode A: native consent prompt, user clicks Yes locally (5.2a).
    // Throws Win32Exception 1223 when the user cancels.
    public static Process LaunchInteractive(string pipeName)
    {
        string exe = Environment.ProcessPath ?? throw new InvalidOperationException("No process path.");
        ProcessStartInfo psi = new()
        {
            FileName = exe,
            Arguments = $"--install-service --pipe \"{pipeName}\"",
            UseShellExecute = true,
            Verb = "runas",
        };
        return Process.Start(psi) ?? throw new InvalidOperationException("Elevated launch failed.");
    }

    // Mode B: admin credentials supplied by the agent (5.2b). The password is
    // used once and zeroed; error codes map to agent-facing messages.
    public static void LaunchWithCredentials(string domain, string username, char[] password, string pipeName)
    {
        string exe = Environment.ProcessPath ?? throw new InvalidOperationException("No process path.");
        string arguments = $"--install-service --pipe \"{pipeName}\"";
        string passwordString = new(password);
        try
        {
            LogonInterop.StartupInfo si = new()
            {
                Cb = Marshal.SizeOf<LogonInterop.StartupInfo>(),
                Desktop = @"WinSta0\Default",
            };
            if (LogonInterop.CreateProcessWithLogon(username, domain, passwordString,
                    LogonInterop.LOGON_WITH_PROFILE, exe, $"\"{exe}\" {arguments}",
                    LogonInterop.CREATE_UNICODE_ENVIRONMENT, IntPtr.Zero, null,
                    ref si, out LogonInterop.ProcessInformation pi))
            {
                _ = LogonInterop.CloseHandle(pi.HProcess);
                _ = LogonInterop.CloseHandle(pi.HThread);
                return;
            }
            int code = Marshal.GetLastWin32Error();
            // Fallback path before giving up (CreateProcessWithLogonW is fussy
            // about station/desktop on some builds).
            if (TryLogonUserFallback(domain, username, passwordString, exe, arguments))
            {
                return;
            }
            throw new Win32Exception(code);
        }
        finally
        {
            // Strings are immutable: keep the managed copy short-lived (method
            // scope only) and deterministically zero the char[] source.
            Array.Clear(password, 0, password.Length);
        }
    }

    private static bool TryLogonUserFallback(string domain, string username, string passwordString, string exe, string arguments)
    {
        if (!LogonInterop.LogonUser(username, domain, passwordString,
                LogonInterop.LOGON32_LOGON_INTERACTIVE, LogonInterop.LOGON32_PROVIDER_DEFAULT, out IntPtr token))
        {
            return false;
        }
        try
        {
            SessionInterop.SecurityAttributes sa = new()
            {
                Length = Marshal.SizeOf<SessionInterop.SecurityAttributes>(),
            };
            LogonInterop.StartupInfo si = new()
            {
                Cb = Marshal.SizeOf<LogonInterop.StartupInfo>(),
                Desktop = @"WinSta0\Default",
            };
            SessionInterop.SecurityAttributes pa = new() { Length = Marshal.SizeOf<SessionInterop.SecurityAttributes>() };
            SessionInterop.SecurityAttributes ta = new() { Length = Marshal.SizeOf<SessionInterop.SecurityAttributes>() };
            if (!SessionInterop.CreateProcessAsUser(token, exe, $"\"{exe}\" {arguments}",
                    ref pa, ref ta, false, SessionInterop.CREATE_UNICODE_ENVIRONMENT,
                    IntPtr.Zero, null, ref si, out LogonInterop.ProcessInformation pi))
            {
                return false;
            }
            _ = LogonInterop.CloseHandle(pi.HProcess);
            _ = LogonInterop.CloseHandle(pi.HThread);
            return true;
        }
        finally
        {
            _ = LogonInterop.CloseHandle(token);
        }
    }
}
