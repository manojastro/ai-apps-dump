// Pre-baked server URL (overridable via textbox and --server CLI).
namespace HelpdeskAnywhere.Applet;

internal sealed class AppOptions
{
    public string ServerUrl { get; init; } = AppConfig.DefaultServerUrl;
    public string Code { get; init; } = "";
    public bool Headless { get; init; }
    public bool AutoAccept { get; init; } = true;
    public int HeadlessStaySeconds { get; init; } = 3;
    public bool Video { get; init; }
    public bool FullFrames { get; init; }
    public bool LogInput { get; init; }
    public string? CheckKey { get; init; }
    public bool InstallService { get; init; }
    public bool UninstallService { get; init; }
    public bool TestLogon { get; init; }
    public bool PipeAclTest { get; init; }
    public string Pipe { get; init; } = "";

    public static AppOptions Parse(string[] args)
    {
        string server = AppConfig.DefaultServerUrl;
        string code = "";
        bool headless = false;
        bool autoAccept = true;
        bool video = false;
        bool fullFrames = false;
        bool logInput = false;
        string? checkKey = null;
        bool installService = false;
        bool uninstallService = false;
        bool testLogon = false;
        bool pipeAclTest = false;
        string pipe = "";
        int stay = 3;
        for (int i = 0; i < args.Length; i++)
        {
            string a = args[i];
            if ((a == "--server" || a == "-s") && i + 1 < args.Length) server = args[++i];
            else if ((a == "--code" || a == "-c") && i + 1 < args.Length) code = args[++i];
            else if (a == "--headless") headless = true;
            else if (a == "--accept") autoAccept = true;
            else if (a == "--decline") autoAccept = false;
            else if (a == "--duration" && i + 1 < args.Length && int.TryParse(args[++i], out int s)) stay = Math.Clamp(s, 1, 120);
            else if (a == "--video") video = true;
            else if (a == "--no-video") video = false;
            else if (a == "--full-frames") fullFrames = true;
            else if (a == "--log-input") logInput = true;
            else if (a == "--check-key" && i + 1 < args.Length) checkKey = args[++i];
            else if (a == "--install-service") installService = true;
            else if (a == "--uninstall-service") uninstallService = true;
            else if (a == "--test-logon") testLogon = true;
            else if (a == "--pipe-acl-test") pipeAclTest = true;
            else if (a == "--pipe" && i + 1 < args.Length) pipe = args[++i];
        }
        return new AppOptions
        {
            ServerUrl = server,
            Code = code.Trim(),
            Headless = headless,
            AutoAccept = autoAccept,
            HeadlessStaySeconds = stay,
            Video = video,
            FullFrames = fullFrames,
            LogInput = logInput,
            CheckKey = checkKey,
            InstallService = installService,
            UninstallService = uninstallService,
            TestLogon = testLogon,
            PipeAclTest = pipeAclTest,
            Pipe = pipe,
        };
    }
}

internal static class AppConfig
{
    // Production default; local dev overrides with ws://127.0.0.1:8080/ws.
    public const string DefaultServerUrl = "wss://helpdesk-anywhere.duckdns.org/ws";
}
