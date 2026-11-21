namespace HelpdeskAnywhere.Applet.Forms;

// Always-visible session indicator (constraint #2): persistent, non-hideable,
// one-click End. Phase 5 adds the elevation notice line to this same window.
internal sealed class SessionIndicator : Form
{
    private readonly Label _mainLabel;
    private readonly Label _noticeLabel;
    private bool _allowClose;

    public SessionIndicator(string agentName)
    {
        string who = string.IsNullOrWhiteSpace(agentName) ? "your agent" : agentName;
        Text = "Helpdesk Anywhere — sharing";
        FormBorderStyle = FormBorderStyle.None;
        TopMost = true;
        ControlBox = false;
        MinimizeBox = false;
        MaximizeBox = false;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.Manual;
        Width = 340;
        Height = 96;

        Panel dot = new()
        {
            BackColor = Color.Red,
            Left = 12,
            Top = 14,
            Width = 12,
            Height = 12,
        };
        _mainLabel = new Label
        {
            Text = $"Screen is being shared with {who}",
            Left = 32,
            Top = 10,
            Width = 296,
            Height = 20,
        };
        _noticeLabel = new Label
        {
            Text = "",
            Left = 32,
            Top = 32,
            Width = 296,
            Height = 20,
            ForeColor = Color.DarkRed,
            Visible = false,
        };
        Button end = new()
        {
            Text = "End Session",
            Left = 32,
            Top = 56,
            Width = 120,
        };
        end.Click += (_, _) =>
        {
            _allowClose = true;
            SessionLifetime.Teardown();
            Close();
        };
        Controls.Add(dot);
        Controls.Add(_mainLabel);
        Controls.Add(_noticeLabel);
        Controls.Add(end);

        Rectangle work = Screen.PrimaryScreen?.WorkingArea ?? new Rectangle(0, 0, 1024, 768);
        Location = new Point(work.Right - Width - 16, work.Bottom - Height - 16);
    }

    public void ShowElevationNotice(string text)
    {
        if (InvokeRequired)
        {
            BeginInvoke(new Action<string>(ShowElevationNotice), text);
            return;
        }
        _noticeLabel.Text = text;
        _noticeLabel.Visible = true;
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        if (!_allowClose && e.CloseReason == CloseReason.UserClosing)
        {
            e.Cancel = true;
            return;
        }
        base.OnFormClosing(e);
    }

    protected override CreateParams CreateParams
    {
        get
        {
            // No minimize/maximize/close affordances on a borderless tool window.
            CreateParams cp = base.CreateParams;
            cp.ClassStyle |= 0x200; // CS_NOCLOSE
            return cp;
        }
    }
}
