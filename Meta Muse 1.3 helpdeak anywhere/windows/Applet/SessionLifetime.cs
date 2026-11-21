// One idempotent Teardown(): stop capture (Phase 3), uninstall service
// (Phase 5), close sockets, remove temp files. A crash must never leave a
// SYSTEM service behind. Phase 2 wires exit paths; Phase 5 fills the
// service-uninstall body.
using Microsoft.Win32;
using HelpdeskAnywhere.Shared.Input;

namespace HelpdeskAnywhere.Applet;

internal static class SessionLifetime
{
    private static int _tornDown;
    private static SessionClient? _client;
    private static IAsyncDisposable? _stream;
    private static InputHandler? _input;
    private static IAsyncDisposable? _bridge;

    public static void Init(SessionClient client)
    {
        _client = client;
        AppDomain.CurrentDomain.ProcessExit += (_, _) => Teardown();
        AppDomain.CurrentDomain.UnhandledException += (_, _) => Teardown();
        try
        {
            Console.CancelKeyPress += (_, e) =>
            {
                e.Cancel = true;
                Teardown();
            };
        }
        catch
        {
            // WinExe has no console; ignore.
        }
        try
        {
            Application.ApplicationExit += (_, _) => Teardown();
            SystemEvents.SessionEnding += (_, _) => Teardown();
        }
        catch
        {
            // SystemEvents unavailable in some contexts; core paths still covered.
        }
    }

    public static void SetStreamer(IAsyncDisposable? stream)
    {
        Interlocked.Exchange(ref _stream, stream);
    }

    public static void SetInputHandler(InputHandler? handler)
    {
        Interlocked.Exchange(ref _input, handler);
    }

    public static void SetBridge(IAsyncDisposable? bridge)
    {
        Interlocked.Exchange(ref _bridge, bridge);
    }

    public static void Teardown()
    {
        if (Interlocked.Exchange(ref _tornDown, 1) == 1) return;
        try
        {
            IAsyncDisposable? bridge = Interlocked.Exchange(ref _bridge, null);
            if (bridge is not null)
            {
                try
                {
                    bridge.DisposeAsync().AsTask().GetAwaiter().GetResult();
                }
                catch
                {
                    // teardown never throws
                }
            }
            // Release held modifiers/buttons first: a drop mid-drag must never
            // leave a stuck key or mouse button on the user's machine.
            InputHandler? handler = Interlocked.Exchange(ref _input, null);
            try
            {
                handler?.ReleaseAll();
            }
            catch
            {
                // teardown never throws
            }
            IAsyncDisposable? stream = Interlocked.Exchange(ref _stream, null);
            if (stream is not null)
            {
                try
                {
                    stream.DisposeAsync().AsTask().GetAwaiter().GetResult();
                }
                catch
                {
                    // teardown never throws
                }
            }
            // Best-effort service removal (5.7): succeeds elevated, silently
            // no-ops otherwise. A crash must never leave a SYSTEM service behind.
            try
            {
                Shared.ServiceManager.Uninstall();
            }
            catch
            {
                // teardown never throws
            }
            SessionClient? client = Interlocked.Exchange(ref _client, null);
            if (client is not null)
            {
                try
                {
                    client.DisposeAsync().AsTask().GetAwaiter().GetResult();
                }
                catch
                {
                    // teardown never throws
                }
            }
        }
        catch
        {
            // teardown never throws
        }
    }

    public static bool IsTornDown => Volatile.Read(ref _tornDown) == 1;
}
