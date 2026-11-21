// Transport: ClientWebSocket to /ws with a separate send queue so that
// video frames (Phase 3) can never block control messages.
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Threading.Channels;
using HelpdeskAnywhere.Shared;

namespace HelpdeskAnywhere.Applet;

internal sealed class ConnectRequestEventArgs(string agentName) : EventArgs
{
    public string AgentName { get; } = agentName;
}

internal sealed class ErrorEventArgs(string error) : EventArgs
{
    public string Error { get; } = error;
}

internal sealed class InputEventArgs(string json) : EventArgs
{
    public string Json { get; } = json;
}

internal sealed class SessionClient : IAsyncDisposable
{
    private readonly ClientWebSocket _ws = new();
    private readonly Channel<string> _controlQueue = Channel.CreateUnbounded<string>();
    private readonly Channel<byte[]> _binaryQueue = Channel.CreateUnbounded<byte[]>();
    private readonly CancellationTokenSource _sendCts = new();
    private Task? _sendLoop;
    private int _sessionEnded; // 1 once ended -> never reconnect
    private int _disposed;

    public event EventHandler<ConnectRequestEventArgs>? ConnectRequest;
    public event EventHandler? PeerJoined;
    public event EventHandler? PeerLeft;
    public event EventHandler<ErrorEventArgs>? ServerError;
    public event EventHandler<InputEventArgs>? AgentInput;
    public event EventHandler<InputEventArgs>? ElevationRequested;
    public event EventHandler? SasRequested;

    public bool SessionEnded => Volatile.Read(ref _sessionEnded) == 1;

    public void MarkEnded() => Interlocked.Exchange(ref _sessionEnded, 1);

    public async Task ConnectAsync(string serverUrl, CancellationToken ct)
    {
        await _ws.ConnectAsync(new Uri(serverUrl), ct).ConfigureAwait(false);
        _sendLoop = Task.Run(SendLoopAsync);
    }

    public async Task JoinAsync(string code, CancellationToken ct)
    {
        string machine = Environment.MachineName;
        string user = Environment.UserName;
        string os = Environment.OSVersion.VersionString;
        var join = new Dictionary<string, object>
        {
            ["t"] = Protocol.MessageTypes.HostJoin,
            ["code"] = code,
            ["machine"] = machine,
            ["user"] = user,
            ["os"] = os,
        };
        await SendControlAsync(JsonSerializer.Serialize(join), ct).ConfigureAwait(false);
    }

    public Task SendConsentAsync(bool accepted, CancellationToken ct)
    {
        var msg = new Dictionary<string, object>
        {
            ["t"] = Protocol.MessageTypes.HostConsent,
            ["accepted"] = accepted,
        };
        return SendControlAsync(JsonSerializer.Serialize(msg), ct);
    }

    public Task SendControlAsync(string json, CancellationToken ct = default)
    {
        return _controlQueue.Writer.WriteAsync(json, ct).AsTask();
    }

    public Task SendBinaryAsync(byte[] payload, CancellationToken ct = default)
    {
        return _binaryQueue.Writer.WriteAsync(payload, ct).AsTask();
    }

    private async Task SendLoopAsync()
    {
        try
        {
            while (!_sendCts.IsCancellationRequested && _ws.State == WebSocketState.Open)
            {
                // Wait for work on EITHER queue, then drain control first so
                // input/consent never starve behind video (without starving video).
                Task<bool> waitControl = _controlQueue.Reader.WaitToReadAsync(_sendCts.Token).AsTask();
                Task<bool> waitBinary = _binaryQueue.Reader.WaitToReadAsync(_sendCts.Token).AsTask();
                try
                {
                    await Task.WhenAny(waitControl, waitBinary).ConfigureAwait(false);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                while (_controlQueue.Reader.TryRead(out string? ctrl))
                {
                    byte[] bytes = Encoding.UTF8.GetBytes(ctrl);
                    await _ws.SendAsync(bytes, WebSocketMessageType.Text, true, _sendCts.Token).ConfigureAwait(false);
                }
                while (_binaryQueue.Reader.TryRead(out byte[]? bin))
                {
                    await _ws.SendAsync(bin, WebSocketMessageType.Binary, true, _sendCts.Token).ConfigureAwait(false);
                }
            }
        }
        catch (OperationCanceledException)
        {
            // shutdown
        }
        catch
        {
            // receive loop observes the close; never throw from sender
        }
    }

    public async Task ReceiveLoopAsync(CancellationToken ct)
    {
        byte[] buffer = new byte[64 * 1024];
        StringBuilder text = new();
        while (!ct.IsCancellationRequested && _ws.State == WebSocketState.Open)
        {
            WebSocketReceiveResult result;
            try
            {
                result = await _ws.ReceiveAsync(buffer, ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
                break;
            }
            if (result.MessageType == WebSocketMessageType.Close)
            {
                MarkEnded();
                break;
            }
            if (result.MessageType == WebSocketMessageType.Binary)
            {
                // Phase 3 consumes binary; Phase 2 drops (server never sends binary to host yet).
                continue;
            }
            text.Clear();
            text.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
            while (!result.EndOfMessage)
            {
                result = await _ws.ReceiveAsync(buffer, ct).ConfigureAwait(false);
                text.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
            }
            try
            {
                DispatchControl(text.ToString());
            }
            catch
            {
                // A faulty message handler must never kill the receive loop.
            }
            if (SessionEnded) break;
        }
    }

    private void DispatchControl(string json)
    {
        string type;
        string agentName = "";
        string error = "";
        try
        {
            using JsonDocument doc = JsonDocument.Parse(json);
            if (!doc.RootElement.TryGetProperty("t", out JsonElement tEl)) return;
            type = tEl.GetString() ?? "";
            if (type == Protocol.MessageTypes.HostConnectRequest &&
                doc.RootElement.TryGetProperty("agentName", out JsonElement aEl))
            {
                agentName = aEl.GetString() ?? "";
            }
            if (type == Protocol.MessageTypes.Error &&
                doc.RootElement.TryGetProperty("error", out JsonElement eEl))
            {
                error = eEl.GetString() ?? "unknown";
            }
        }
        catch (JsonException)
        {
            return;
        }

        if (type == Protocol.MessageTypes.HostConnectRequest)
        {
            ConnectRequest?.Invoke(this, new ConnectRequestEventArgs(agentName));
        }
        else if (type == Protocol.MessageTypes.PeerJoined)
        {
            PeerJoined?.Invoke(this, EventArgs.Empty);
        }
        else if (type == Protocol.MessageTypes.PeerLeft)
        {
            MarkEnded();
            PeerLeft?.Invoke(this, EventArgs.Empty);
        }
        else if (type == Protocol.MessageTypes.Error)
        {
            ServerError?.Invoke(this, new ErrorEventArgs(error));
        }
        else if (type == Protocol.MessageTypes.AgentInput)
        {
            // Remote-control payload for InputHandler (Phase 4). Relayed by the
            // server only while the session is active.
            AgentInput?.Invoke(this, new InputEventArgs(json));
        }
        else if (type == Protocol.MessageTypes.AgentRequestElevation)
        {
            ElevationRequested?.Invoke(this, new InputEventArgs(json));
        }
        else if (type == Protocol.MessageTypes.AgentSas)
        {
            SasRequested?.Invoke(this, EventArgs.Empty);
        }
    }

    public async ValueTask DisposeAsync()
    {
        if (Interlocked.Exchange(ref _disposed, 1) == 1) return;
        MarkEnded();
        try
        {
            _sendCts.Cancel();
        }
        catch (ObjectDisposedException)
        {
            // already torn down
        }
        try
        {
            if (_ws.State == WebSocketState.Open)
            {
                using CancellationTokenSource cts = new(TimeSpan.FromSeconds(2));
                await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "bye", cts.Token).ConfigureAwait(false);
            }
        }
        catch
        {
            // ignore close errors during teardown
        }
        _ws.Dispose();
        _sendCts.Dispose();
        GC.SuppressFinalize(this);
    }
}
