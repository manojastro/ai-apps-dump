using System.Drawing.Imaging;
using HelpdeskAnywhere.Shared.Capture;
using HelpdeskAnywhere.Shared.Imaging;

namespace HelpdeskAnywhere.Applet.Streaming;

// Dirty-rect streamer (Phase 3.3): 128x128 tiles, FNV-1a hash per tile over
// locked 32bpp rows, changed tiles as [0x02][x:u16be][y:u16be][w:u16be][h:u16be][jpeg].
// Full [0x01] keyframe every 5s and on start. Tile coords are relative to the
// virtual-desktop origin so the browser canvas starts at (0,0).
// Typically cuts bandwidth 10-20x on a mostly-static desktop.
internal sealed class DirtyRectStreamer : IAsyncDisposable
{
    public const int TileSize = 128;
    public const int KeyframeIntervalSeconds = 5;

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
    private ulong[] _prevHashes = [];
    private int _gridW;
    private int _gridH;
    private DateTime _lastKeyframe = DateTime.MinValue;

    public DirtyRectStreamer(SessionClient client, IScreenCapture capture, int fps = 9, long quality = 60, Action<string>? logger = null)
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
            if (Interlocked.CompareExchange(ref _sending, 1, 0) == 1) continue;
            try
            {
                List<byte[]> frames = await Task.Run(CaptureAndDiff, _cts.Token).ConfigureAwait(false);
                foreach (byte[] frame in frames)
                {
                    await _client.SendBinaryAsync(frame, _cts.Token).ConfigureAwait(false);
                }
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                if (Interlocked.Exchange(ref _loggedError, 1) == 0)
                    Log($"dirty-rect failed: {ex.GetType().Name} in {ex.TargetSite?.Name}: {ex.Message}");
            }
            finally
            {
                Volatile.Write(ref _sending, 0);
            }
        }
    }

    private List<byte[]> CaptureAndDiff()
    {
        using Bitmap bmp = _capture.Grab();
        int w = bmp.Width;
        int h = bmp.Height;
        int gridW = (w + TileSize - 1) / TileSize;
        int gridH = (h + TileSize - 1) / TileSize;
        if (gridW != _gridW || gridH != _gridH)
        {
            _gridW = gridW;
            _gridH = gridH;
            _prevHashes = new ulong[gridW * gridH];
            _lastKeyframe = DateTime.MinValue; // force keyframe on resize
        }
        bool wantKeyframe = DateTime.UtcNow - _lastKeyframe >= TimeSpan.FromSeconds(KeyframeIntervalSeconds);
        if (wantKeyframe)
        {
            byte[] jpeg = JpegEncoder.Encode(bmp, _quality);
            byte[] frame = new byte[jpeg.Length + 1];
            frame[0] = 0x01;
            Buffer.BlockCopy(jpeg, 0, frame, 1, jpeg.Length);
            _lastKeyframe = DateTime.UtcNow;
            UpdateHashes(bmp);
            return [frame];
        }
        List<byte[]> out_frames = [];
        Rectangle lockRect = new(0, 0, w, h);
        BitmapData data = bmp.LockBits(lockRect, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        try
        {
            unsafe
            {
                byte* basePtr = (byte*)data.Scan0;
                int stride = data.Stride;
                for (int ty = 0; ty < gridH; ty++)
                {
                    for (int tx = 0; tx < gridW; tx++)
                    {
                        int x = tx * TileSize;
                        int y = ty * TileSize;
                        int tw = Math.Min(TileSize, w - x);
                        int th = Math.Min(TileSize, h - y);
                        ulong hash = HashTile(basePtr, stride, x, y, tw, th);
                        int idx = ty * gridW + tx;
                        if (hash == _prevHashes[idx]) continue;
                        _prevHashes[idx] = hash;
                        using Bitmap tile = bmp.Clone(new Rectangle(x, y, tw, th), PixelFormat.Format32bppArgb);
                        byte[] jpeg = JpegEncoder.Encode(tile, _quality);
                        byte[] frame = new byte[jpeg.Length + 9];
                        frame[0] = 0x02;
                        frame[1] = (byte)((x >> 8) & 0xFF);
                        frame[2] = (byte)(x & 0xFF);
                        frame[3] = (byte)((y >> 8) & 0xFF);
                        frame[4] = (byte)(y & 0xFF);
                        frame[5] = (byte)((tw >> 8) & 0xFF);
                        frame[6] = (byte)(tw & 0xFF);
                        frame[7] = (byte)((th >> 8) & 0xFF);
                        frame[8] = (byte)(th & 0xFF);
                        Buffer.BlockCopy(jpeg, 0, frame, 9, jpeg.Length);
                        out_frames.Add(frame);
                    }
                }
            }
        }
        finally
        {
            bmp.UnlockBits(data);
        }
        return out_frames;
    }

    private void UpdateHashes(Bitmap bmp)
    {
        Rectangle lockRect = new(0, 0, bmp.Width, bmp.Height);
        BitmapData data = bmp.LockBits(lockRect, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        try
        {
            unsafe
            {
                byte* basePtr = (byte*)data.Scan0;
                int stride = data.Stride;
                for (int ty = 0; ty < _gridH; ty++)
                {
                    for (int tx = 0; tx < _gridW; tx++)
                    {
                        int x = tx * TileSize;
                        int y = ty * TileSize;
                        _prevHashes[ty * _gridW + tx] = HashTile(
                            basePtr, stride, x, y,
                            Math.Min(TileSize, bmp.Width - x),
                            Math.Min(TileSize, bmp.Height - y));
                    }
                }
            }
        }
        finally
        {
            bmp.UnlockBits(data);
        }
    }

    private static unsafe ulong HashTile(byte* basePtr, int stride, int x, int y, int w, int h)
    {
        // FNV-1a 64 over the tile rows (32bpp => 4 bytes/pixel).
        const ulong offset = 14695981039346656037ul;
        const ulong prime = 1099511628211ul;
        ulong hash = offset;
        for (int row = 0; row < h; row++)
        {
            ulong* pixels = (ulong*)(basePtr + ((y + row) * stride) + (x * 4));
            int quads = (w * 4) / 8;
            for (int i = 0; i < quads; i++)
            {
                hash ^= pixels[i];
                hash *= prime;
            }
        }
        return hash;
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
