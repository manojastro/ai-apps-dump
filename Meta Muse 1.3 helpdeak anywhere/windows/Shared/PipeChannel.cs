using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;

namespace HelpdeskAnywhere.Shared;

// Named-pipe IPC between Applet (server) and DesktopHelper/installer (clients).
// Frames are length-prefixed (Int32 little-endian) raw payloads: video frames
// pass through untouched ([0x01]/[0x02]), control messages are JSON ('{').
// The ACL admits only LocalSystem and the current user — a world-writable pipe
// into a SYSTEM process would be a local privilege-escalation hole.
public static class PipeChannel
{
    public const string Prefix = "hda-";
    public const int MaxFrameBytes = 12 * 1024 * 1024;

    public static string GetPipeName(string sessionId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sessionId);
        return $"{Prefix}{sessionId}";
    }

    public static string GeneratePipeName()
    {
        return $"{Prefix}{Guid.NewGuid():N}";
    }

    public static bool LooksLikeVideo(byte[] frame)
    {
        return frame.Length > 0 && (frame[0] == 0x01 || frame[0] == 0x02);
    }

    public static PipeSecurity CreateSecurity()
    {
        PipeSecurity security = new();
        security.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(WellKnownSidType.LocalSystemSid, null),
            PipeAccessRights.FullControl, AccessControlType.Allow));
        SecurityIdentifier? user = WindowsIdentity.GetCurrent().User;
        if (user is not null)
        {
            security.AddAccessRule(new PipeAccessRule(
                user, PipeAccessRights.FullControl, AccessControlType.Allow));
        }
        return security;
    }
}

public sealed class PipeServer : IDisposable
{
    private readonly NamedPipeServerStream _server;
    private bool _disposed;

    public PipeServer(string pipeName)
    {
        // ACL-capable construction lives on NamedPipeServerStreamAcl in .NET.
        _server = NamedPipeServerStreamAcl.Create(
            pipeName, PipeDirection.InOut, 1,
            PipeTransmissionMode.Byte, PipeOptions.Asynchronous,
            65536, 65536, PipeChannel.CreateSecurity(), HandleInheritability.None);
    }

    public Task WaitForConnectionAsync(CancellationToken ct)
    {
        return _server.WaitForConnectionAsync(ct);
    }

    public bool IsConnected => _server.IsConnected;

    public List<string> GetAccessRules()
    {
        List<string> lines = [];
        PipeSecurity security = _server.GetAccessControl();
        foreach (PipeAccessRule? rule in security.GetAccessRules(true, true, typeof(SecurityIdentifier)))
        {
            if (rule.IdentityReference is null) continue;
            string name;
            try
            {
                name = rule.IdentityReference.Translate(typeof(NTAccount)).ToString();
            }
            catch (IdentityNotMappedException)
            {
                name = rule.IdentityReference.Value ?? "?";
            }
            lines.Add($"{name}:{rule.PipeAccessRights}:{rule.AccessControlType}");
        }
        return lines;
    }

    public async Task<byte[]?> ReadFrameAsync(CancellationToken ct)
    {
        byte[]? lenBuf = await ReadExactAsync(4, ct).ConfigureAwait(false);
        if (lenBuf is null) return null;
        int length = BitConverter.ToInt32(lenBuf, 0);
        if (length <= 0 || length > PipeChannel.MaxFrameBytes) return null;
        return await ReadExactAsync(length, ct).ConfigureAwait(false);
    }

    public async Task WriteFrameAsync(byte[] payload, CancellationToken ct)
    {
        byte[] len = BitConverter.GetBytes(payload.Length);
        await _server.WriteAsync(len, ct).ConfigureAwait(false);
        await _server.WriteAsync(payload, ct).ConfigureAwait(false);
        await _server.FlushAsync(ct).ConfigureAwait(false);
    }

    public void Disconnect()
    {
        try
        {
            if (_server.IsConnected) _server.Disconnect();
        }
        catch (InvalidOperationException)
        {
            // already disconnected
        }
    }

    private async Task<byte[]?> ReadExactAsync(int count, CancellationToken ct)
    {
        byte[] buf = new byte[count];
        int read = 0;
        while (read < count)
        {
            int n;
            try
            {
                n = await _server.ReadAsync(buf.AsMemory(read, count - read), ct).ConfigureAwait(false);
            }
            catch (IOException)
            {
                return null;
            }
            if (n == 0) return null;
            read += n;
        }
        return buf;
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _server.Dispose();
        GC.SuppressFinalize(this);
    }
}

public sealed class PipeClient : IDisposable
{
    private readonly NamedPipeClientStream _client;
    private bool _disposed;

    public PipeClient(string pipeName)
    {
        _client = new NamedPipeClientStream(".", pipeName, PipeDirection.InOut, PipeOptions.Asynchronous);
    }

    public async Task ConnectAsync(int timeoutMs, CancellationToken ct)
    {
        using CancellationTokenSource linked = CancellationTokenSource.CreateLinkedTokenSource(ct);
        linked.CancelAfter(timeoutMs);
        await _client.ConnectAsync(linked.Token).ConfigureAwait(false);
    }

    public async Task<byte[]?> ReadFrameAsync(CancellationToken ct)
    {
        byte[]? lenBuf = await ReadExactAsync(4, ct).ConfigureAwait(false);
        if (lenBuf is null) return null;
        int length = BitConverter.ToInt32(lenBuf, 0);
        if (length <= 0 || length > PipeChannel.MaxFrameBytes) return null;
        return await ReadExactAsync(length, ct).ConfigureAwait(false);
    }

    public async Task WriteFrameAsync(byte[] payload, CancellationToken ct)
    {
        byte[] len = BitConverter.GetBytes(payload.Length);
        await _client.WriteAsync(len, ct).ConfigureAwait(false);
        await _client.WriteAsync(payload, ct).ConfigureAwait(false);
        await _client.FlushAsync(ct).ConfigureAwait(false);
    }

    private async Task<byte[]?> ReadExactAsync(int count, CancellationToken ct)
    {
        byte[] buf = new byte[count];
        int read = 0;
        while (read < count)
        {
            int n;
            try
            {
                n = await _client.ReadAsync(buf.AsMemory(read, count - read), ct).ConfigureAwait(false);
            }
            catch (IOException)
            {
                return null;
            }
            if (n == 0) return null;
            read += n;
        }
        return buf;
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _client.Dispose();
        GC.SuppressFinalize(this);
    }
}
