// Binds one session's secure-desktop path (5.6): the per-session pipe,
// elevation requests, helper video forwarding, input routing, SAS, and
// host.desktopChanged notifications. The caller owns local capture + UI and
// supplies small callbacks; the bridge owns pipe + elevation + secure flag.
using System.Text.Json;
using HelpdeskAnywhere.Shared;

namespace HelpdeskAnywhere.Applet.Elevation;

internal sealed class SecureBridge : IAsyncDisposable
{
    private static readonly string SasJson =
        JsonSerializer.Serialize(new { t = Protocol.MessageTypes.AgentSas });

    private readonly SessionClient _client;
    private readonly Func<string, Task> _sendControl;
    private readonly Action _onSecureActive;
    private readonly Action _onSecureGone;
    private readonly Action<string> _notice;
    private readonly Action<string> _localInput;
    private readonly PipeHost _pipe;
    private readonly ElevationSession _elevation;
    private readonly SemaphoreSlim _switchGate = new(1, 1);
    private int _disposed;

    public bool SecureActive { get; private set; }
    public string SecureDesktop { get; private set; } = "Default";
    public string PipeName => _pipe.PipeName;
    public bool Elevated => _elevation.Elevated;

    public SecureBridge(
        SessionClient client,
        string serverUrl,
        Func<string, Task> sendControl,
        Action<string> localInput,
        Action onSecureActive,
        Action onSecureGone,
        Action<string> notice,
        Action<string>? pipeLog = null)
    {
        _client = client;
        _sendControl = sendControl;
        _localInput = localInput;
        _onSecureActive = onSecureActive;
        _onSecureGone = onSecureGone;
        _notice = notice;
        bool tls = serverUrl.StartsWith("wss://", StringComparison.OrdinalIgnoreCase);
        _pipe = new PipeHost(PipeChannel.GeneratePipeName(), pipeLog);
        _elevation = new ElevationSession(client, _pipe, tls);
        _elevation.Notice += (_, msg) => SafeNotice(msg);
        _client.ElevationRequested += (_, e) => _ = HandleElevationSafelyAsync(e.Json);
        _client.AgentInput += (_, e) => RouteInput(e.Json);
        _client.SasRequested += (_, _) => RouteSas();
        _pipe.VideoFrame += (_, frame) =>
        {
            _ = SendVideoSafelyAsync(frame);
            if (!SecureActive) _ = ActivateAsync("Winlogon");
        };
        _pipe.HelperReady += (_, e) => _ = ActivateAsync(e.Desktop);
        _pipe.HelperGone += (_, _) => _ = DeactivateAsync();
    }

    public void Start() => _pipe.Start();

    private async Task HandleElevationSafelyAsync(string json)
    {
        try
        {
            await _elevation.HandleRequestAsync(json).ConfigureAwait(false);
        }
        catch
        {
            // elevation handling never faults the session
        }
    }

    private void RouteInput(string json)
    {
        try
        {
            if (SecureActive && _pipe.HelperConnected)
            {
                _ = WritePipeSafelyAsync(json);
                return;
            }
            _localInput(json);
        }
        catch
        {
            // routing never throws
        }
    }

    private void RouteSas()
    {
        try
        {
            if (SecureActive && _pipe.HelperConnected)
            {
                _ = WritePipeSafelyAsync(SasJson);
            }
        }
        catch
        {
            // routing never throws
        }
    }

    private async Task SendVideoSafelyAsync(byte[] frame)
    {
        try
        {
            await _client.SendBinaryAsync(frame).ConfigureAwait(false);
        }
        catch
        {
            // forwarding never throws
        }
    }

    private async Task WritePipeSafelyAsync(string json)
    {
        try
        {
            using CancellationTokenSource cts = new(TimeSpan.FromSeconds(5));
            await _pipe.WriteInputAsync(json, cts.Token).ConfigureAwait(false);
        }
        catch
        {
            // pipe writes never throw into the session
        }
    }

    private async Task ActivateAsync(string desktop)
    {
        if (SecureActive) return;
        await _switchGate.WaitAsync().ConfigureAwait(false);
        try
        {
            if (SecureActive) return;
            SecureActive = true;
            SecureDesktop = desktop;
            try
            {
                _onSecureActive();
            }
            catch
            {
                // caller callbacks never break the bridge
            }
            await SendDesktopChangedAsync(desktop).ConfigureAwait(false);
        }
        finally
        {
            _switchGate.Release();
        }
    }

    private async Task DeactivateAsync()
    {
        if (!SecureActive) return;
        await _switchGate.WaitAsync().ConfigureAwait(false);
        try
        {
            if (!SecureActive) return;
            SecureActive = false;
            SecureDesktop = "Default";
            try
            {
                _onSecureGone();
            }
            catch
            {
                // caller callbacks never break the bridge
            }
            await SendDesktopChangedAsync("Default").ConfigureAwait(false);
        }
        finally
        {
            _switchGate.Release();
        }
    }

    private async Task SendDesktopChangedAsync(string desktop)
    {
        try
        {
            string json = JsonSerializer.Serialize(new { t = "host.desktopChanged", desktop });
            await _sendControl(json).ConfigureAwait(false);
        }
        catch
        {
            // notification is best effort
        }
    }

    private void SafeNotice(string message)
    {
        try
        {
            _notice(message);
        }
        catch
        {
            // notices never throw
        }
    }

    public async ValueTask DisposeAsync()
    {
        if (Interlocked.Exchange(ref _disposed, 1) == 1) return;
        try
        {
            await _pipe.DisposeAsync().ConfigureAwait(false);
        }
        catch
        {
            // shutdown path never throws
        }
        _switchGate.Dispose();
        GC.SuppressFinalize(this);
    }
}
