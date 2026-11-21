namespace HelpdeskAnywhere.Applet.Forms;

internal sealed class ConsentDialog : Form
{
    private bool _decided;

    public ConsentDialog(string agentName, SessionClient client)
    {
        ArgumentNullException.ThrowIfNull(client);
        Text = "Support request";
        StartPosition = FormStartPosition.CenterScreen;
        TopMost = true;
        ControlBox = false;
        MinimizeBox = false;
        MaximizeBox = false;
        KeyPreview = true;
        Width = 440;
        Height = 200;
        FormBorderStyle = FormBorderStyle.FixedDialog;

        string who = string.IsNullOrWhiteSpace(agentName) ? "Your agent" : agentName;
        Label prompt = new()
        {
            Text = $"\"{who}\" is requesting to view and control this computer.",
            Left = 16,
            Top = 20,
            Width = 396,
            Height = 60,
        };
        Button accept = new() { Text = "Accept", Left = 220, Top = 110, Width = 90, DialogResult = DialogResult.None };
        Button decline = new() { Text = "Decline", Left = 320, Top = 110, Width = 90, DialogResult = DialogResult.None };
        accept.Click += async (_, _) => await DecideAsync(true, client).ConfigureAwait(false);
        decline.Click += async (_, _) => await DecideAsync(false, client).ConfigureAwait(false);
        Controls.Add(prompt);
        Controls.Add(accept);
        Controls.Add(decline);
    }

    protected override bool ProcessDialogKey(Keys keyData)
    {
        // Consent must not be dismissible via Esc.
        if (keyData == Keys.Escape) return true;
        return base.ProcessDialogKey(keyData);
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        // Force an explicit Accept/Decline; ignore Alt+F4 / system close.
        if (!_decided && e.CloseReason == CloseReason.UserClosing)
        {
            e.Cancel = true;
            return;
        }
        base.OnFormClosing(e);
    }

    private async Task DecideAsync(bool accepted, SessionClient client)
    {
        _decided = true;
        try
        {
            using CancellationTokenSource cts = new(TimeSpan.FromSeconds(10));
            await client.SendConsentAsync(accepted, cts.Token).ConfigureAwait(false);
        }
        catch
        {
            // consent send failure still closes; server close handler ends the session
        }
        if (!accepted)
        {
            SessionLifetime.Teardown();
        }
        BeginInvoke(new Action(() =>
        {
            DialogResult = accepted ? DialogResult.OK : DialogResult.Cancel;
            Close();
        }));
    }
}
