// Applet-side named-pipe server (5.5): one per-session pipe accepting the
// elevated installer first, then the DesktopHelper. Video frames pass through
// untouched; JSON control frames are dispatched (install.result, helper.ready).
using System.Text;
using System.Text.Json;
using HelpdeskAnywhere.Shared;

namespace HelpdeskAnywhere.Applet.Elevation;

internal sealed class InstallResultEventArgs(bool ok, string error) : EventArgs
{
    public bool Ok { get; } = ok;
    public string Error { get; } = error;
}

internal sealed class HelperReadyEventArgs(string desktop) : EventArgs
{
    public string Desktop { get; } = desktop;
}

internal sealed class PipeHost : IAsyncDisposable
{
    private readonly PipeServer _server;
    private readonly CancellationTokenSource _cts = new();
    private Task? _acceptLoop;
    private int _disposed;

    public string PipeName { get; }

    private readonly Action<string>? _logger;

    public event EventHandler<byte[]>? VideoFrame;
    public event EventHandler<HelperReadyEventArgs>? HelperReady;
    public event EventHandler? HelperGone;

    private TaskCompletionSource<InstallResultEventArgs> _installTcs =
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    public PipeHost(string pipeName, Action<string>? logger = null)
    {
        PipeName = pipeName;
        _logger = logger;
        _server = new PipeServer(pipeName);
    }

    public void Start() => _acceptLoop = Task.Run(AcceptLoopAsync);

    public Task<InstallResultEventArgs> WaitInstallResultAsync(CancellationToken ct)
    {
        return _installTcs.Task.WaitAsync(ct);
    }

    public void ResetInstallResult()
    {
        _installTcs = new(TaskCreationOptions.RunContinuationsAsynchronously);
    }

    public async Task WriteInputAsync(string json, CancellationToken ct)
    {
        if (!_server.IsConnected) return;
        await _server.WriteFrameAsync(Encoding.UTF8.GetBytes(json), ct).ConfigureAwait(false);
    }

    public bool HelperConnected => _server.IsConnected;

    private async Task AcceptLoopAsync()
    {
        while (!_cts.IsCancellationRequested)
        {
            bool helperSession = false;
            try
            {
                await _server.WaitForConnectionAsync(_cts.Token).ConfigureAwait(false);
                Log("pipe: client connected");
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
                // A faulted listen must not kill the server: reset the
                // instance and keep listening (a break here would wedge the
                // pipe busy forever for all future helpers/installers).
                try
                {
                    _server.Disconnect();
                }
                catch
                {
                    // reset is best effort
                }
                try
                {
                    await Task.Delay(250, _cts.Token).ConfigureAwait(false);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                continue;
            }
            try
            {
                // Handshake gate: the first frame must be install.result or
                // helper.ready within 10s. Silent squatters (AV probes, stray
                // processes) are dropped so the instance frees for the helper.
                byte[]? first = await ReadFirstFrameAsync().ConfigureAwait(false);
                if (first is null) continue; // shutdown or squat; loop decides
                if (PipeChannel.LooksLikeVideo(first))
                {
                    VideoFrame?.Invoke(this, first);
                }
                else
                {
                    string kind = Classify(first);
                    if (kind == "install.result")
                    {
                        (bool ok, string error) = ParseInstallResult(first);
                        _installTcs.TrySetResult(new InstallResultEventArgs(ok, error));
                    }
                    else if (kind == "helper.ready")
                    {
                        helperSession = true;
                        HelperReady?.Invoke(this, new HelperReadyEventArgs(ParseDesktop(first)));
                    }
                    else
                    {
                        continue; // unknown opener; drop without events
                    }
                }
                while (!_cts.IsCancellationRequested)
                {
                    byte[]? frame = await _server.ReadFrameAsync(_cts.Token).ConfigureAwait(false);
                    if (frame is null) break;
                    if (PipeChannel.LooksLikeVideo(frame))
                    {
                        VideoFrame?.Invoke(this, frame);
                        continue;
                    }
                    string kind = Classify(frame);
                    if (kind == "install.result")
                    {
                        (bool ok, string error) = ParseInstallResult(frame);
                        _installTcs.TrySetResult(new InstallResultEventArgs(ok, error));
                    }
                    else if (kind == "helper.ready")
                    {
                        helperSession = true;
                        HelperReady?.Invoke(this, new HelperReadyEventArgs(ParseDesktop(frame)));
                    }
                }
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
                // client I/O failures end this client, not the server
            }
            finally
            {
                _server.Disconnect();
                if (helperSession)
                {
                    helperSession = false;
                    HelperGone?.Invoke(this, EventArgs.Empty);
                }
            }
        }
    }

    private async Task<byte[]?> ReadFirstFrameAsync()
    {
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(10));
        using CancellationTokenSource linked = CancellationTokenSource.CreateLinkedTokenSource(_cts.Token, timeout.Token);
        try
        {
            return await _server.ReadFrameAsync(linked.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException) when (!timeout.IsCancellationRequested)
        {
            throw; // real shutdown; outer loop breaks
        }
        catch (OperationCanceledException)
        {
            try
            {
                _logger?.Invoke("pipe: dropped silent client");
            }
            catch
            {
                // logging never throws
            }
            return null;
        }
    }

    private void Log(string message)
    {
        try
        {
            _logger?.Invoke(message);
        }
        catch
        {
            // logging never throws
        }
    }

    private static string Classify(byte[] frame)
    {
        try
        {
            using JsonDocument doc = JsonDocument.Parse(Encoding.UTF8.GetString(frame));
            if (doc.RootElement.TryGetProperty("t", out JsonElement t))
            {
                return t.GetString() ?? "";
            }
        }
        catch (JsonException)
        {
            // not JSON; ignore
        }
        return "";
    }

    private static (bool ok, string error) ParseInstallResult(byte[] frame)
    {
        try
        {
            using JsonDocument doc = JsonDocument.Parse(Encoding.UTF8.GetString(frame));
            bool ok = doc.RootElement.TryGetProperty("ok", out JsonElement okEl) && okEl.GetBoolean();
            string error = doc.RootElement.TryGetProperty("error", out JsonElement eEl) ? eEl.GetString() ?? "" : "";
            return (ok, error);
        }
        catch (JsonException)
        {
            return (false, "bad install reply");
        }
    }

    private static string ParseDesktop(byte[] frame)
    {
        try
        {
            using JsonDocument doc = JsonDocument.Parse(Encoding.UTF8.GetString(frame));
            if (doc.RootElement.TryGetProperty("desktop", out JsonElement d))
            {
                return d.GetString() ?? "Winlogon";
            }
        }
        catch (JsonException)
        {
            // fall through
        }
        return "Winlogon";
    }

    public async ValueTask DisposeAsync()
    {
        if (Interlocked.Exchange(ref _disposed, 1) == 1) return;
        _cts.Cancel();
        if (_acceptLoop is not null)
        {
            try
            {
                await _acceptLoop.WaitAsync(TimeSpan.FromSeconds(3)).ConfigureAwait(false);
            }
            catch
            {
                // shutdown path never throws
            }
        }
        _cts.Dispose();
        _server.Dispose();
        GC.SuppressFinalize(this);
    }
}
