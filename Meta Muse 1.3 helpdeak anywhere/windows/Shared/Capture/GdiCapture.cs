using System.Drawing;
using System.Runtime.InteropServices;
using HelpdeskAnywhere.Shared.Capture.Interop;

namespace HelpdeskAnywhere.Shared.Capture;

// GDI capture over the full virtual desktop (multi-monitor extents).
// Handles are reused across frames: recreating them per frame drops to ~3 FPS.
// BitBlt does not include the cursor, so it is blitted manually.
public sealed class GdiCapture : IScreenCapture
{
    private IntPtr _screenDc = IntPtr.Zero;
    private IntPtr _memDc = IntPtr.Zero;
    private IntPtr _bitmap = IntPtr.Zero;
    private IntPtr _oldBitmap = IntPtr.Zero;
    private int _x;
    private int _y;
    private int _width;
    private int _height;
    private bool _disposed;

    public Size Bounds => new(_width, _height);

    public Bitmap Grab()
    {
        EnsureHandles();
        const int rop = GdiInterop.SRCCOPY | GdiInterop.CAPTUREBLT;
        if (!GdiInterop.BitBlt(_memDc, 0, 0, _width, _height, _screenDc, _x, _y, rop))
        {
            throw new InvalidOperationException("BitBlt failed during screen capture.");
        }
        DrawCursor();
        // FromHbitmap copies the HBITMAP into a managed Bitmap; caller disposes it.
        return Image.FromHbitmap(_bitmap);
    }

    private void EnsureHandles()
    {
        int x = GdiInterop.GetSystemMetrics(GdiInterop.SM_XVIRTUALSCREEN);
        int y = GdiInterop.GetSystemMetrics(GdiInterop.SM_YVIRTUALSCREEN);
        int w = GdiInterop.GetSystemMetrics(GdiInterop.SM_CXVIRTUALSCREEN);
        int h = GdiInterop.GetSystemMetrics(GdiInterop.SM_CYVIRTUALSCREEN);
        if (w <= 0 || h <= 0)
        {
            throw new InvalidOperationException("No display bounds reported.");
        }
        if (_screenDc != IntPtr.Zero && x == _x && y == _y && w == _width && h == _height)
        {
            return;
        }
        ReleaseHandles();
        _x = x;
        _y = y;
        _width = w;
        _height = h;
        _screenDc = GdiInterop.CreateDC("DISPLAY", null, null, IntPtr.Zero);
        if (_screenDc == IntPtr.Zero)
        {
            throw new InvalidOperationException("CreateDC(DISPLAY) failed.");
        }
        _memDc = GdiInterop.CreateCompatibleDC(_screenDc);
        if (_memDc == IntPtr.Zero)
        {
            throw new InvalidOperationException("CreateCompatibleDC failed.");
        }
        _bitmap = GdiInterop.CreateCompatibleBitmap(_screenDc, _width, _height);
        if (_bitmap == IntPtr.Zero)
        {
            throw new InvalidOperationException("CreateCompatibleBitmap failed.");
        }
        _oldBitmap = GdiInterop.SelectObject(_memDc, _bitmap);
    }

    private void DrawCursor()
    {
        GdiInterop.CursorInfo ci = new() { cbSize = Marshal.SizeOf<GdiInterop.CursorInfo>() };
        if (!GdiInterop.GetCursorInfo(ref ci)) return;
        if ((ci.flags & GdiInterop.CURSOR_SHOWING) == 0 || ci.hCursor == IntPtr.Zero) return;
        int cx = ci.ptScreenPos.X - _x;
        int cy = ci.ptScreenPos.Y - _y;
        _ = GdiInterop.DrawIconEx(_memDc, cx, cy, ci.hCursor, 0, 0, 0, IntPtr.Zero, GdiInterop.DI_NORMAL);
    }

    private void ReleaseHandles()
    {
        if (_memDc != IntPtr.Zero && _oldBitmap != IntPtr.Zero)
        {
            _ = GdiInterop.SelectObject(_memDc, _oldBitmap);
            _oldBitmap = IntPtr.Zero;
        }
        if (_bitmap != IntPtr.Zero)
        {
            _ = GdiInterop.DeleteObject(_bitmap);
            _bitmap = IntPtr.Zero;
        }
        if (_memDc != IntPtr.Zero)
        {
            _ = GdiInterop.DeleteDC(_memDc);
            _memDc = IntPtr.Zero;
        }
        if (_screenDc != IntPtr.Zero)
        {
            _ = GdiInterop.DeleteDC(_screenDc);
            _screenDc = IntPtr.Zero;
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        ReleaseHandles();
        GC.SuppressFinalize(this);
    }
}
