using System.Drawing;
using System.Drawing.Imaging;

namespace HelpdeskAnywhere.Shared.Imaging;

public static class JpegEncoder
{
    private static readonly ImageCodecInfo JpegCodec =
        ImageCodecInfo.GetImageEncoders().First(c => c.FormatID == ImageFormat.Jpeg.Guid);

    public static byte[] Encode(Bitmap bitmap, long quality = 60)
    {
        long q = Math.Clamp(quality, 40, 75);
        using EncoderParameters parameters = new(1);
        parameters.Param[0] = new EncoderParameter(Encoder.Quality, q);
        using MemoryStream ms = new();
        bitmap.Save(ms, JpegCodec, parameters);
        return ms.ToArray();
    }
}
