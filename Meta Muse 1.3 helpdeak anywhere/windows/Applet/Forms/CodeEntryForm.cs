using System.Text.RegularExpressions;

namespace HelpdeskAnywhere.Applet.Forms;

internal sealed partial class CodeEntryForm : Form
{
    private readonly TextBox _serverBox;
    private readonly TextBox _codeBox;
    private readonly Button _connectButton;
    private readonly Label _errorLabel;

    public SessionClient? ConnectedClient { get; private set; }
    public string AgentName { get; private set; } = "";
    public string ServerUrl => _serverBox.Text.Trim();
    public string Code => _codeBox.Text.Trim();

    public CodeEntryForm(string initialServerUrl, string initialCode)
    {
        Text = "Helpdesk Anywhere — Join support session";
        StartPosition = FormStartPosition.CenterScreen;
        Width = 420;
        Height = 260;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;

        Label serverLabel = new() { Text = "Server:", Left = 16, Top = 20, Width = 60 };
        _serverBox = new TextBox { Left = 90, Top = 16, Width = 300, Text = initialServerUrl };

        Label codeLabel = new() { Text = "Code:", Left = 16, Top = 60, Width = 60 };
        _codeBox = new TextBox { Left = 90, Top = 56, Width = 120, MaxLength = 6, Text = initialCode };

        _connectButton = new Button { Text = "Connect", Left = 220, Top = 54, Width = 90 };
        _connectButton.Click += ConnectButton_Click;

        _errorLabel = new Label
        {
            Left = 16,
            Top = 100,
            Width = 374,
            Height = 60,
            ForeColor = Color.Red,
            Text = "",
        };

        Label hint = new()
        {
            Left = 16,
            Top = 165,
            Width = 374,
            Height = 50,
            Text = "Enter the 6-digit code from your agent, then Connect.",
        };

        Controls.Add(serverLabel);
        Controls.Add(_serverBox);
        Controls.Add(codeLabel);
        Controls.Add(_codeBox);
        Controls.Add(_connectButton);
        Controls.Add(_errorLabel);
        Controls.Add(hint);
        AcceptButton = _connectButton;
    }

    private static partial class Regexes
    {
        [GeneratedRegex("^[0-9]{6}$")]
        public static partial Regex SixDigit();
    }

    private async void ConnectButton_Click(object? sender, EventArgs e)
    {
        _errorLabel.Text = "";
        string code = Code;
        string server = ServerUrl;
        if (!Regexes.SixDigit().IsMatch(code))
        {
            _errorLabel.Text = "Enter the 6-digit code from your agent.";
            return;
        }
        if (!Uri.TryCreate(server, UriKind.Absolute, out Uri? uri) ||
            (uri.Scheme != "ws" && uri.Scheme != "wss"))
        {
            _errorLabel.Text = "Server URL must start with ws:// or wss:// and end with /ws.";
            return;
        }
        _connectButton.Enabled = false;
        _codeBox.Enabled = false;
        _serverBox.Enabled = false;
        try
        {
            await AttemptJoinAsync(server, code).ConfigureAwait(true);
        }
        finally
        {
            if (ConnectedClient is null)
            {
                _connectButton.Enabled = true;
                _codeBox.Enabled = true;
                _serverBox.Enabled = true;
            }
        }
    }

    private async Task AttemptJoinAsync(string server, string code)
    {
        SessionClient client = new();
        TaskCompletionSource<string> gotAgent = new(TaskCreationOptions.RunContinuationsAsynchronously);
        TaskCompletionSource<string> gotError = new(TaskCreationOptions.RunContinuationsAsynchronously);
        void OnConnectRequest(object? s, ConnectRequestEventArgs e) => gotAgent.TrySetResult(e.AgentName);
        void OnError(object? s, ErrorEventArgs e) => gotError.TrySetResult(e.Error);
        client.ConnectRequest += OnConnectRequest;
        client.ServerError += OnError;
        try
        {
            using CancellationTokenSource cts = new(TimeSpan.FromSeconds(20));
            await client.ConnectAsync(server, cts.Token).ConfigureAwait(false);
            _ = client.ReceiveLoopAsync(cts.Token);
            await client.JoinAsync(code, cts.Token).ConfigureAwait(false);
            Task completed = await Task.WhenAny(gotAgent.Task, gotError.Task).WaitAsync(cts.Token).ConfigureAwait(false);
            if (completed == gotError.Task)
            {
                string err = FriendlyError(await gotError.Task.ConfigureAwait(false));
                ShowError(err);
                await client.DisposeAsync().ConfigureAwait(false);
                return;
            }
            string agent = await gotAgent.Task.ConfigureAwait(false);
            ConnectedClient = client;
            AgentName = agent;
            // Hand off to Program message loop (UI thread).
            BeginInvoke(new Action(Close));
        }
        catch (OperationCanceledException)
        {
            ShowError("Timed out waiting for the server. Check the server URL and try again.");
            await client.DisposeAsync().ConfigureAwait(false);
        }
        catch (Exception ex) when (ex is UriFormatException || ex is System.Net.WebSockets.WebSocketException || ex is HttpRequestException)
        {
            ShowError("Could not reach the server. Check the server URL and try again.");
            await client.DisposeAsync().ConfigureAwait(false);
        }
        finally
        {
            client.ConnectRequest -= OnConnectRequest;
            client.ServerError -= OnError;
        }
    }

    private static string FriendlyError(string raw) => raw switch
    {
        "invalid_code" => "That code was not recognized. Check the 6 digits and try again.",
        "expired" => "That code has expired. Ask your agent for a fresh code.",
        "rate_limited" => "Too many attempts. Wait a minute and try again.",
        _ => "The server refused the connection. Ask your agent for a fresh code.",
    };

    private void ShowError(string text)
    {
        if (InvokeRequired)
        {
            BeginInvoke(new Action<string>(ShowError), text);
            return;
        }
        _errorLabel.Text = text;
    }
}
