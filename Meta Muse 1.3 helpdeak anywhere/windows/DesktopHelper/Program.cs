// Secure-desktop worker: runs as SYSTEM inside the interactive session,
// attached to one desktop (--desktop Winlogon). SetThreadDesktop runs BEFORE
// any window, DC, or bitmap is created — the association is per-thread and
// fixed at handle-creation time. Reuses Shared capture + input; streams full
// frames over the applet pipe and injects input (incl. SendSAS) from it.
using System.Drawing;
using System.Text;
using System.Text.Json;
using HelpdeskAnywhere.Shared;
using HelpdeskAnywhere.Shared.Capture;
using HelpdeskAnywhere.Shared.Imaging;
using HelpdeskAnywhere.Shared.Input;
using HelpdeskAnywhere.Shared.Interop;

namespace HelpdeskAnywhere.DesktopHelper;

internal static class Program
{
    private static int Main(string[] args)
    {
        string desktop = Arg(args, "--desktop") ?? "";
        string pipe = Arg(args, "--pipe") ?? "";
        if (desktop.Length == 0 || pipe.Length == 0)
        {
            Console.Error.WriteLine("usage: DesktopHelper --desktop <name> --pipe <name>");
            return 2;
        }
        // FIRST: join the target desktop before creating any handle.
        IntPtr hDesk = DesktopInterop.OpenDesktop(desktop, 0, false, DesktopInterop.GENERIC_ALL);
        if (hDesk == IntPtr.Zero)
        {
            Console.Error.WriteLine($"open desktop {desktop} failed");
            return 1;
        }
        if (!DesktopInterop.SetThreadDesktop(hDesk))
        {
            Console.Error.WriteLine($"attach {desktop} failed");
            _ = DesktopInterop.CloseDesktop(hDesk);
            return 1;
        }
        try
        {
            return RunAsync(desktop, pipe).GetAwaiter().GetResult();
        }
        finally
        {
            _ = DesktopInterop.CloseDesktop(hDesk);
        }
    }

    private static async Task<int> RunAsync(string desktop, string pipeName)
    {
        using CancellationTokenSource cts = new();
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            cts.Cancel();
        };
        using GdiCapture capture = new();
        InputHandler input = new();
        // InputHandler wraps the same injector instance methods; route pipe JSON through it.
        using PipeClient pipe = new(pipeName);
        try
        {
            // Generous timeout: a pipe squatter (e.g. AV inspection) may hold
            // the single instance until the applet's 10s handshake drop frees it.
            await pipe.ConnectAsync(30000, cts.Token).ConfigureAwait(false);
        }
        catch
        {
            Console.Error.WriteLine("pipe connect timeout");
            return 1;
        }
        try
        {
            string ready = JsonSerializer.Serialize(new { t = "helper.ready", desktop });
            await pipe.WriteFrameAsync(Encoding.UTF8.GetBytes(ready), cts.Token).ConfigureAwait(false);
        }
        catch
        {
            return 1;
        }
        Task readTask = Task.Run(() => ReadLoopAsync(pipe, input, cts.Token));
        Task captureTask = Task.Run(() => CaptureLoopAsync(pipe, capture, cts.Token));
        await Task.WhenAny(readTask, captureTask).ConfigureAwait(false);
        cts.Cancel();
        try
        {
            await Task.WhenAll(readTask, captureTask).ConfigureAwait(false);
        }
        catch
        {
            // shutdown races are normal
        }
        try
        {
            input.ReleaseAll();
        }
        catch
        {
            // release path never throws
        }
        return 0;
    }

    private static async Task ReadLoopAsync(PipeClient pipe, InputHandler input, CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            byte[]? frame = await pipe.ReadFrameAsync(ct).ConfigureAwait(false);
            if (frame is null) return; // applet gone
            if (PipeChannel.LooksLikeVideo(frame)) continue;
            string json;
            try
            {
                json = Encoding.UTF8.GetString(frame);
            }
            catch
            {
                continue;
            }
            if (IsSas(json))
            {
                try
                {
                    DesktopInterop.SendSAS(true);
                }
                catch
                {
                    // best effort; the prompt stays for local dismissal
                }
                continue;
            }
            input.OnAgentInput(json);
        }
    }

    private static async Task CaptureLoopAsync(PipeClient pipe, GdiCapture capture, CancellationToken ct)
    {
        using PeriodicTimer timer = new(TimeSpan.FromMilliseconds(125)); // ~8 FPS
        int sending = 0;
        while (await timer.WaitForNextTickAsync(ct).ConfigureAwait(false))
        {
            if (Interlocked.CompareExchange(ref sending, 1, 0) == 1) continue;
            try
            {
                byte[] frame = await Task.Run(() =>
                {
                    using Bitmap bmp = capture.Grab();
                    byte[] jpeg = JpegEncoder.Encode(bmp, 50);
                    byte[] f = new byte[jpeg.Length + 1];
                    f[0] = 0x01;
                    Buffer.BlockCopy(jpeg, 0, f, 1, jpeg.Length);
                    return f;
                }, ct).ConfigureAwait(false);
                await pipe.WriteFrameAsync(frame, ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch
            {
                // degrade (skip) rather than die
            }
            finally
            {
                Volatile.Write(ref sending, 0);
            }
        }
    }

    private static bool IsSas(string json)
    {
        try
        {
            using JsonDocument doc = JsonDocument.Parse(json);
            return doc.RootElement.TryGetProperty("t", out JsonElement t) &&
                t.GetString() == "agent.sas";
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static string? Arg(string[] args, string name)
    {
        for (int i = 0; i < args.Length; i++)
        {
            if (string.Equals(args[i], name, StringComparison.OrdinalIgnoreCase) && i + 1 < args.Length)
            {
                return args[i + 1];
            }
        }
        return null;
    }
}
