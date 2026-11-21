using HelpdeskAnywhere.Shared.Capture;
using HelpdeskAnywhere.Shared.Imaging;

namespace HelpdeskAnywhere.Applet.Streaming;

// Full-frame streamer (Phase 3.2): fixed-rate timer, JPEG quality 60,
// [0x01][jpeg] binary frames. Skips a tick while the previous send has not
// completed so a slow link degrades frame rate instead of queueing.
internal sealed class FrameStreamer : IAsyncDisposable
{
    private readonly SessionClient _client;
    private readonly IScreenCapture _capture;
    private readonly int _fps;
    private readonly long _quality;
    private readonly Action<string>? _logger;
    private readonly CancellationTokenSource _cts = new();
    private Task? _loop;
    private int _sending;
    private int _disposed;
    private int _loggedError;
    private int _loggedOk;

    public FrameStreamer(SessionClient client, IScreenCapture capture, int fps = 9, long quality = 60, Action<string>? logger = null)
    {
        _client = client;
        _capture = capture;
        _fps = Math.Clamp(fps, 1, 15);
        _quality = Math.Clamp(quality, 40, 75);
        _logger = logger;
    }

    public void Start() => _loop = Task.Run(LoopAsync);

    private async Task LoopAsync()
    {
        using PeriodicTimer timer = new(TimeSpan.FromMilliseconds(1000.0 / _fps));
        while (await timer.WaitForNextTickAsync(_cts.Token).ConfigureAwait(false))
        {
            if (_client.SessionEnded || _cts.IsCancellationRequested) break;
            // Skip this frame if the previous send has not completed.
            if (Interlocked.CompareExchange(ref _sending, 1, 0) == 1) continue;
            try
            {
                byte[] frame = await Task.Run(CaptureAndEncode, _cts.Token).ConfigureAwait(false);
                await _client.SendBinaryAsync(frame, _cts.Token).ConfigureAwait(false);
                if (Interlocked.Exchange(ref _loggedOk, 1) == 0) Log($"first frame queued ({frame.Length} bytes)");
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                // Capture/encode/send failures degrade (skip) rather than kill the session.
                if (Interlocked.Exchange(ref _loggedError, 1) == 0) Log($"capture/send failed: {ex.GetType().Name} in {ex.TargetSite?.Name}: {ex.Message}");
            }
            finally
            {
                Volatile.Write(ref _sending, 0);
            }
        }
    }

    private byte[] CaptureAndEncode()
    {
        using Bitmap bmp = _capture.Grab();
        byte[] jpeg = JpegEncoder.Encode(bmp, _quality);
        byte[] frame = new byte[jpeg.Length + 1];
        frame[0] = 0x01;
        Buffer.BlockCopy(jpeg, 0, frame, 1, jpeg.Length);
        return frame;
    }

    private void Log(string message)
    {
        try
        {
            _logger?.Invoke(message);
        }
        catch
        {
            // logging never breaks streaming
        }
    }

    public async ValueTask DisposeAsync()
    {
        if (Interlocked.Exchange(ref _disposed, 1) == 1) return;
        _cts.Cancel();
        if (_loop is not null)
        {
            try
            {
                await _loop.WaitAsync(TimeSpan.FromSeconds(3)).ConfigureAwait(false);
            }
            catch
            {
                // shutdown path never throws
            }
        }
        _cts.Dispose();
        _capture.Dispose();
        GC.SuppressFinalize(this);
    }
}
