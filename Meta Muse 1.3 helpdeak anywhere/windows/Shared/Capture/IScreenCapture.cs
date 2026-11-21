using System.Drawing;
namespace HelpdeskAnywhere.Shared.Capture;

public interface IScreenCapture : IDisposable
{
    Size Bounds { get; }
    Bitmap Grab();
}
