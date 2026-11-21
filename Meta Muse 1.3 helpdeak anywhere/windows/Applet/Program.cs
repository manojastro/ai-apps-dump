using HelpdeskAnywhere.Shared.Capture;
using HelpdeskAnywhere.Applet.Elevation;
using HelpdeskAnywhere.Applet.Forms;
using HelpdeskAnywhere.Shared.Input;
using HelpdeskAnywhere.Applet.Streaming;

namespace HelpdeskAnywhere.Applet;

internal static class Program
{
    [STAThread]
    private static int Main(string[] args)
    {
        AppOptions options = AppOptions.Parse(args);
        if (options.CheckKey is not null)
        {
            return RunCheckKey(options.CheckKey);
        }
        if (options.InstallService)
        {
            return Installer.RunInstallService(options.Pipe);
        }
        if (options.UninstallService)
        {
            return Installer.RunUninstallService();
        }
        if (options.TestLogon)
        {
            return Installer.RunTestLogon();
        }
        if (options.PipeAclTest)
        {
            return RunPipeAclTest();
        }
        if (options.Headless)
        {
            return RunHeadlessAsync(options).GetAwaiter().GetResult();
        }
        ApplicationConfiguration.Initialize();
        Application.ThreadException += (_, _) => SessionLifetime.Teardown();
        return RunGui(options);
    }

    private static int RunGui(AppOptions options)
    {
        SessionClient? client;
        string agent;
        using (CodeEntryForm entry = new(options.ServerUrl, options.Code))
        {
            Application.Run(entry);
            client = entry.ConnectedClient;
            agent = entry.AgentName;
        }
        if (client is null)
        {
            return 0;
        }
        SessionLifetime.Init(client);
        string agentName = agent;
        using ConsentDialog consent = new(agentName, client);
        DialogResult choice = consent.ShowDialog();
        if (choice != DialogResult.OK)
        {
            return 0;
        }
        DirtyRectStreamer? localVideo = null;
        void StartLocalVideo()
        {
            StopLocalVideo();
            DirtyRectStreamer streamer = new(client, new GdiCapture());
            SessionLifetime.SetStreamer(streamer);
            streamer.Start();
            localVideo = streamer;
        }
        void StopLocalVideo()
        {
            SessionLifetime.SetStreamer(null);
            try
            {
                localVideo?.DisposeAsync().AsTask().GetAwaiter().GetResult();
            }
            catch
            {
                // shutdown path never throws
            }
            finally
            {
                localVideo = null;
            }
        }
        InputHandler input = new();
        SessionLifetime.SetInputHandler(input);
        client.PeerLeft += (_, _) => input.ReleaseAll();
        using SessionIndicator indicator = new(agentName);
        // If the peer drops, close the indicator so the app exits.
        client.PeerLeft += (_, _) =>
        {
            try
            {
                indicator.BeginInvoke(new Action(indicator.Close));
            }
            catch
            {
                // indicator may already be disposed during teardown
            }
        };
        SecureBridge bridge = new(
            client,
            options.ServerUrl,
            sendControl: json => client.SendControlAsync(json),
            localInput: json => input.OnAgentInput(json),
            onSecureActive: StopLocalVideo,
            onSecureGone: StartLocalVideo,
            notice: msg =>
            {
                try
                {
                    indicator.ShowElevationNotice(msg);
                }
                catch
                {
                    // notices never throw
                }
            });
        SessionLifetime.SetBridge(bridge);
        bridge.Start();
        StartLocalVideo();
        try
        {
            Application.Run(indicator);
        }
        finally
        {
            SessionLifetime.SetBridge(null);
            try
            {
                bridge.DisposeAsync().AsTask().GetAwaiter().GetResult();
            }
            catch
            {
                // shutdown path never throws
            }
            StopLocalVideo();
            SessionLifetime.SetInputHandler(null);
            input.ReleaseAll();
            SessionLifetime.Teardown();
        }
        return 0;
    }

    // TEST-ONLY pipe ACL self-test: creates a real PipeServer, reads back the
    // applied descriptor in-process (no timing races), and asserts only
    // LocalSystem + current user are admitted.
    private static int RunPipeAclTest()
    {
        string name = Shared.PipeChannel.GeneratePipeName();
        using Shared.PipeServer server = new(name);
        var rules = server.GetAccessRules();
        foreach (string line in rules)
        {
            Console.WriteLine($"acl: {line}");
        }
        bool system = false;
        bool self = false;
        bool stranger = false;
        string me = System.Security.Principal.WindowsIdentity.GetCurrent().Name ?? "";
        foreach (string line in rules)
        {
            if (line.StartsWith("NT AUTHORITY\\SYSTEM:", StringComparison.OrdinalIgnoreCase)) system = true;
            else if (me.Length > 0 && line.StartsWith(me + ":", StringComparison.OrdinalIgnoreCase)) self = true;
            else stranger = true;
        }
        bool ok = system && self && !stranger;
        Console.WriteLine(ok ? "acl: RESTRICTED" : "acl: UNEXPECTED");
        return ok ? 0 : 1;
    }

    // Table self-test (no UI, no injection): prints event.code -> VK mapping.
    // Accepts comma-separated codes so callers need only one process spawn.
    private static int RunCheckKey(string codes)
    {
        int bad = 0;
        foreach (string part in codes.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            if (KeyMap.TryGet(part, out KeyMap.Entry entry))
            {
                Console.WriteLine($"{part} -> VK 0x{entry.Vk:X2} ext {entry.Extended.ToString().ToLowerInvariant()}");
            }
            else
            {
                Console.Error.WriteLine($"{part}: unknown");
                bad++;
            }
        }
        return bad == 0 ? 0 : 2;
    }

    // Headless transport check (automated tests only, no UI):
    // join -> wait connectRequest -> consent -> wait peer.joined -> linger -> exit 0.
    private static async Task<int> RunHeadlessAsync(AppOptions options)
    {
        if (!System.Text.RegularExpressions.Regex.IsMatch(options.Code, "^[0-9]{6}$"))
        {
            Console.Error.WriteLine("headless: --code must be 6 digits");
            return 2;
        }
        await using SessionClient client = new();
        SessionLifetime.Init(client);
        // Test-only receipt log (headless --log-input): kinds + physical codes,
        // never anything the session carries beyond that. CI uses synthetic input.
        InputHandler input = new(options.LogInput ? m => Console.WriteLine($"headless: {m}") : null);
        SessionLifetime.SetInputHandler(input);
        client.PeerLeft += (_, _) => input.ReleaseAll();
        IAsyncDisposable? localVideo = null;
        void StartLocalVideo()
        {
            if (!options.Video) return;
            StopLocalVideo();
            Action<string> log = m => Console.WriteLine($"headless: stream: {m}");
            IAsyncDisposable streamer = options.FullFrames
                ? new FrameStreamer(client, new GdiCapture(), logger: log)
                : new DirtyRectStreamer(client, new GdiCapture(), logger: log);
            SessionLifetime.SetStreamer(streamer);
            if (streamer is FrameStreamer full) full.Start();
            else if (streamer is DirtyRectStreamer dirty) dirty.Start();
            localVideo = streamer;
            Console.WriteLine("headless: streaming video");
        }
        void StopLocalVideo()
        {
            SessionLifetime.SetStreamer(null);
            try
            {
                localVideo?.DisposeAsync().AsTask().GetAwaiter().GetResult();
            }
            catch
            {
                // shutdown path never throws
            }
            finally
            {
                localVideo = null;
            }
        }
        SecureBridge bridge = new(
            client,
            options.ServerUrl,
            sendControl: json => client.SendControlAsync(json),
            localInput: json => input.OnAgentInput(json),
            onSecureActive: StopLocalVideo,
            onSecureGone: StartLocalVideo,
            notice: m => Console.WriteLine($"headless: notice: {m}"),
            pipeLog: options.LogInput ? m => Console.WriteLine($"headless: {m}") : null);
        SessionLifetime.SetBridge(bridge);
        bridge.Start();
        TaskCompletionSource<string> gotAgent = new(TaskCreationOptions.RunContinuationsAsynchronously);
        TaskCompletionSource<string> gotError = new(TaskCreationOptions.RunContinuationsAsynchronously);
        TaskCompletionSource<bool> gotPeer = new(TaskCreationOptions.RunContinuationsAsynchronously);
        client.ConnectRequest += (_, e) => gotAgent.TrySetResult(e.AgentName);
        client.ServerError += (_, e) => gotError.TrySetResult(e.Error);
        client.PeerJoined += (_, _) => gotPeer.TrySetResult(true);
        try
        {
            using CancellationTokenSource cts = new(TimeSpan.FromSeconds(Math.Min(options.HeadlessStaySeconds + 25, 180)));
            await client.ConnectAsync(options.ServerUrl, cts.Token).ConfigureAwait(false);
            _ = client.ReceiveLoopAsync(cts.Token);
            await client.JoinAsync(options.Code, cts.Token).ConfigureAwait(false);
            Task first = await Task.WhenAny(gotAgent.Task, gotError.Task).WaitAsync(cts.Token).ConfigureAwait(false);
            if (first == gotError.Task)
            {
                Console.Error.WriteLine($"headless: join refused: {await gotError.Task.ConfigureAwait(false)}");
                return 2;
            }
            string agent = await gotAgent.Task.ConfigureAwait(false);
            Console.WriteLine($"headless: connectRequest from '{agent}'");
            await client.SendConsentAsync(options.AutoAccept, cts.Token).ConfigureAwait(false);
            Console.WriteLine($"headless: sent consent:{options.AutoAccept.ToString().ToLowerInvariant()}");
            if (!options.AutoAccept) return 0;
            await gotPeer.Task.WaitAsync(cts.Token).ConfigureAwait(false);
            Console.WriteLine("headless: peer.joined (active)");
            Console.WriteLine($"headless: pipe {bridge.PipeName}");
            StartLocalVideo();
            try
            {
                await Task.Delay(TimeSpan.FromSeconds(options.HeadlessStaySeconds), cts.Token).ConfigureAwait(false);
            }
            finally
            {
                SessionLifetime.SetBridge(null);
                try
                {
                    await bridge.DisposeAsync().ConfigureAwait(false);
                }
                catch
                {
                    // shutdown path never throws
                }
                StopLocalVideo();
                SessionLifetime.SetInputHandler(null);
                input.ReleaseAll();
            }
            return 0;
        }
        catch (Exception ex) when (ex is OperationCanceledException or TimeoutException)
        {
            Console.Error.WriteLine("headless: timed out");
            return 1;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"headless: {ex.GetType().Name}");
            return 1;
        }
        finally
        {
            SessionLifetime.Teardown();
        }
    }
}
