using System.Runtime.InteropServices;
using HelpdeskAnywhere.Shared.Input.Interop;

namespace HelpdeskAnywhere.Shared.Input;

// Reusable Win32 input injector (Phases 4 + 5 share this class: the elevated
// helper reuses it on the secure desktop). All P/Invoke lives in Interop/.
public sealed class InputInjector
{
    private const int NormalizationMax = 65535;
    private const int WheelDelta = 120;

    public void MoveTo(int x, int y)
    {
        (int absX, int absY) = ToAbsolute(x, y);
        SendMouse(absX, absY, 0,
            InputInterop.MOUSEEVENTF_MOVE | InputInterop.MOUSEEVENTF_ABSOLUTE | InputInterop.MOUSEEVENTF_VIRTUALDESK);
    }

    public void MouseDown(string button, int x, int y)
    {
        (int absX, int absY) = ToAbsolute(x, y);
        uint flag = button switch
        {
            "middle" => InputInterop.MOUSEEVENTF_MIDDLEDOWN,
            "right" => InputInterop.MOUSEEVENTF_RIGHTDOWN,
            _ => InputInterop.MOUSEEVENTF_LEFTDOWN,
        };
        SendMouse(absX, absY, 0, flag | InputInterop.MOUSEEVENTF_ABSOLUTE | InputInterop.MOUSEEVENTF_VIRTUALDESK);
    }

    public void MouseUp(string button, int x, int y)
    {
        (int absX, int absY) = ToAbsolute(x, y);
        uint flag = button switch
        {
            "middle" => InputInterop.MOUSEEVENTF_MIDDLEUP,
            "right" => InputInterop.MOUSEEVENTF_RIGHTUP,
            _ => InputInterop.MOUSEEVENTF_LEFTUP,
        };
        SendMouse(absX, absY, 0, flag | InputInterop.MOUSEEVENTF_ABSOLUTE | InputInterop.MOUSEEVENTF_VIRTUALDESK);
    }

    public void Wheel(int dx, int dy)
    {
        // DOM deltas arrive down/right-positive; Windows wheel is up-positive.
        if (dy != 0)
        {
            SendMouse(0, 0, (uint)Math.Clamp(-dy, -WheelDelta * 10, WheelDelta * 10), InputInterop.MOUSEEVENTF_WHEEL);
        }
        if (dx != 0)
        {
            SendMouse(0, 0, (uint)Math.Clamp(-dx, -WheelDelta * 10, WheelDelta * 10), InputInterop.MOUSEEVENTF_HWHEEL);
        }
    }

    public bool KeyDown(string code) => KeyEvent(code, up: false);

    public bool KeyUp(string code) => KeyEvent(code, up: true);

    private static bool KeyEvent(string code, bool up)
    {
        if (!KeyMap.TryGet(code, out KeyMap.Entry entry)) return false;
        uint scancode = InputInterop.MapVirtualKey(entry.Vk, InputInterop.MAPVK_VK_TO_VSC);
        if (scancode == 0) return false;
        uint flags = InputInterop.KEYEVENTF_SCANCODE;
        if (entry.Extended) flags |= InputInterop.KEYEVENTF_EXTENDEDKEY;
        if (up) flags |= InputInterop.KEYEVENTF_KEYUP;
        InputInterop.InputUnit[] inputs =
        [
            new()
            {
                Type = InputInterop.INPUT_KEYBOARD,
                U = new InputInterop.InputUnion
                {
                    Ki = new InputInterop.KeybdInput
                    {
                        WVk = 0,
                        WScan = (ushort)scancode,
                        DwFlags = flags,
                    },
                },
            },
        ];
        return InputInterop.SendInput(1, inputs, Marshal.SizeOf<InputInterop.InputUnit>()) == 1;
    }

    private static void SendMouse(int dx, int dy, uint data, uint flags)
    {
        InputInterop.InputUnit[] inputs =
        [
            new()
            {
                Type = InputInterop.INPUT_MOUSE,
                U = new InputInterop.InputUnion
                {
                    Mi = new InputInterop.MouseInput
                    {
                        Dx = dx,
                        Dy = dy,
                        MouseData = data,
                        DwFlags = flags,
                    },
                },
            },
        ];
        _ = InputInterop.SendInput(1, inputs, Marshal.SizeOf<InputInterop.InputUnit>());
    }

    private static (int absX, int absY) ToAbsolute(int x, int y)
    {
        int originX = InputInterop.GetSystemMetrics(InputInterop.SM_XVIRTUALSCREEN);
        int originY = InputInterop.GetSystemMetrics(InputInterop.SM_YVIRTUALSCREEN);
        int width = Math.Max(1, InputInterop.GetSystemMetrics(InputInterop.SM_CXVIRTUALSCREEN));
        int height = Math.Max(1, InputInterop.GetSystemMetrics(InputInterop.SM_CYVIRTUALSCREEN));
        // 0-65535 virtual-desktop space; origin offset keeps multi-monitor exact.
        int absX = Math.Clamp((x - originX) * NormalizationMax / width, 0, NormalizationMax);
        int absY = Math.Clamp((y - originY) * NormalizationMax / height, 0, NormalizationMax);
        return (absX, absY);
    }
}
