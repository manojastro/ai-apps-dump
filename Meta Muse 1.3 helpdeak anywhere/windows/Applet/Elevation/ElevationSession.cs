// Handles agent.requestElevation for one session (5.2). Rate-limits to 5
// attempts; refuses credential mode without TLS; surfaces progress on the
// session indicator; reports host.elevated. Passwords are char[]-only,
// single-use, zeroed — never logged, never sent anywhere but the one launch call.
using System.ComponentModel;
using System.Text.Json;
using HelpdeskAnywhere.Shared;

namespace HelpdeskAnywhere.Applet.Elevation;

internal sealed class ElevationSession
{
    private const int MaxAttemptsPerSession = 5;

    private readonly SessionClient _client;
    private readonly PipeHost _pipe;
    private readonly bool _tls;
    private int _attempts;

    public bool Elevated { get; private set; }

    public event EventHandler<string>? Notice;

    public ElevationSession(SessionClient client, PipeHost pipe, bool tls)
    {
        _client = client;
        _pipe = pipe;
        _tls = tls;
    }

    public async Task HandleRequestAsync(string json)
    {
        int attempt = Interlocked.Increment(ref _attempts);
        if (attempt > MaxAttemptsPerSession)
        {
            await SendElevatedAsync(false, "rate_limited").ConfigureAwait(false);
            return;
        }
        string mode;
        string domain;
        string username;
        string passwordText;
        try
        {
            using JsonDocument doc = JsonDocument.Parse(json);
            JsonElement root = doc.RootElement;
            mode = root.TryGetProperty("mode", out JsonElement m) ? m.GetString() ?? "" : "";
            domain = root.TryGetProperty("domain", out JsonElement d) ? d.GetString() ?? "" : "";
            username = root.TryGetProperty("username", out JsonElement u) ? u.GetString() ?? "" : "";
            passwordText = root.TryGetProperty("password", out JsonElement p) ? p.GetString() ?? "" : "";
        }
        catch (JsonException)
        {
            await SendElevatedAsync(false, "bad_message").ConfigureAwait(false);
            return;
        }
        if (mode == "credential" && !_tls)
        {
            // Defense in depth: the server already refuses this without TLS.
            await SendElevatedAsync(false, "tls_required").ConfigureAwait(false);
            return;
        }
        Notice?.Invoke(this, "The agent is elevating privileges on this computer.");
        try
        {
            if (mode == "interactive")
            {
                await RunInteractiveAsync().ConfigureAwait(false);
            }
            else if (mode == "credential")
            {
                char[] password = passwordText.ToCharArray();
                passwordText = "";
                try
                {
                    await RunCredentialAsync(domain, username, password).ConfigureAwait(false);
                }
                finally
                {
                    Array.Clear(password, 0, password.Length);
                }
            }
            else
            {
                await SendElevatedAsync(false, "bad_message").ConfigureAwait(false);
            }
        }
        finally
        {
            passwordText = "";
        }
    }

    private async Task RunInteractiveAsync()
    {
        _pipe.ResetInstallResult();
        try
        {
            using (Installer.LaunchInteractive(_pipe.PipeName))
            {
            }
        }
        catch (Win32Exception ex) when (ex.NativeErrorCode == ElevationErrors.Cancelled)
        {
            await SendElevatedAsync(false, "declined").ConfigureAwait(false);
            return;
        }
        catch (Exception)
        {
            await SendElevatedAsync(false, "launch_failed").ConfigureAwait(false);
            return;
        }
        await AwaitInstallResultAsync().ConfigureAwait(false);
    }

    private async Task RunCredentialAsync(string domain, string username, char[] password)
    {
        _pipe.ResetInstallResult();
        try
        {
            await Task.Run(() => Installer.LaunchWithCredentials(domain, username, password, _pipe.PipeName)).ConfigureAwait(false);
        }
        catch (Win32Exception ex)
        {
            await SendElevatedAsync(false, ElevationErrors.ToMessage(ex.NativeErrorCode)).ConfigureAwait(false);
            return;
        }
        catch (Exception)
        {
            await SendElevatedAsync(false, "launch_failed").ConfigureAwait(false);
            return;
        }
        await AwaitInstallResultAsync().ConfigureAwait(false);
    }

    private async Task AwaitInstallResultAsync()
    {
        InstallResultEventArgs result;
        try
        {
            using CancellationTokenSource cts = new(TimeSpan.FromSeconds(120));
            result = await _pipe.WaitInstallResultAsync(cts.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            await SendElevatedAsync(false, "timeout").ConfigureAwait(false);
            return;
        }
        catch (TimeoutException)
        {
            await SendElevatedAsync(false, "timeout").ConfigureAwait(false);
            return;
        }
        if (result.Ok)
        {
            Elevated = true;
            Notice?.Invoke(this, "Running with elevated privileges.");
            await SendElevatedAsync(true, "").ConfigureAwait(false);
        }
        else
        {
            await SendElevatedAsync(false, result.Error.Length > 0 ? result.Error : "install_failed").ConfigureAwait(false);
        }
    }

    private async Task SendElevatedAsync(bool ok, string error)
    {
        try
        {
            string json = ok
                ? JsonSerializer.Serialize(new { t = Protocol.MessageTypes.HostElevated, ok = true })
                : JsonSerializer.Serialize(new { t = Protocol.MessageTypes.HostElevated, ok = false, error });
            await _client.SendControlAsync(json).ConfigureAwait(false);
        }
        catch
        {
            // result reporting is best effort once the session is ending
        }
    }
}
