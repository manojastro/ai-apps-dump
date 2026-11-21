namespace HelpdeskAnywhere.Shared.Input;

// Explicit DOM event.code (physical key) -> Windows VK table. Layout-independent
// by design: shifted symbols arrive as modifier+digit pairs from the portal.
// Extended=true for the E0-prefixed set: arrows, Ins/Del/Home/End/PgUp/PgDn,
// right Alt/Ctrl, numpad Enter/Divide, Meta keys, Apps, PrintScreen, NumLock.
public static class KeyMap
{
    public readonly record struct Entry(byte Vk, bool Extended);

    public static bool IsModifier(string code) =>
        code is "ShiftLeft" or "ShiftRight" or "ControlLeft" or "ControlRight"
            or "AltLeft" or "AltRight" or "MetaLeft" or "MetaRight";

    private static readonly Dictionary<string, Entry> Table = new(StringComparer.Ordinal)
    {
        // Letters
        ["KeyA"] = new(0x41, false), ["KeyB"] = new(0x42, false), ["KeyC"] = new(0x43, false),
        ["KeyD"] = new(0x44, false), ["KeyE"] = new(0x45, false), ["KeyF"] = new(0x46, false),
        ["KeyG"] = new(0x47, false), ["KeyH"] = new(0x48, false), ["KeyI"] = new(0x49, false),
        ["KeyJ"] = new(0x4A, false), ["KeyK"] = new(0x4B, false), ["KeyL"] = new(0x4C, false),
        ["KeyM"] = new(0x4D, false), ["KeyN"] = new(0x4E, false), ["KeyO"] = new(0x4F, false),
        ["KeyP"] = new(0x50, false), ["KeyQ"] = new(0x51, false), ["KeyR"] = new(0x52, false),
        ["KeyS"] = new(0x53, false), ["KeyT"] = new(0x54, false), ["KeyU"] = new(0x55, false),
        ["KeyV"] = new(0x56, false), ["KeyW"] = new(0x57, false), ["KeyX"] = new(0x58, false),
        ["KeyY"] = new(0x59, false), ["KeyZ"] = new(0x5A, false),
        // Top-row digits
        ["Digit0"] = new(0x30, false), ["Digit1"] = new(0x31, false), ["Digit2"] = new(0x32, false),
        ["Digit3"] = new(0x33, false), ["Digit4"] = new(0x34, false), ["Digit5"] = new(0x35, false),
        ["Digit6"] = new(0x36, false), ["Digit7"] = new(0x37, false), ["Digit8"] = new(0x38, false),
        ["Digit9"] = new(0x39, false),
        // Symbols (unshifted positions; shift arrives as a modifier)
        ["Minus"] = new(0xBD, false), ["Equal"] = new(0xBB, false),
        ["BracketLeft"] = new(0xDB, false), ["BracketRight"] = new(0xDD, false),
        ["Backslash"] = new(0xDC, false), ["Semicolon"] = new(0xBA, false),
        ["Quote"] = new(0xDE, false), ["Backquote"] = new(0xC0, false),
        ["Comma"] = new(0xBC, false), ["Period"] = new(0xBE, false), ["Slash"] = new(0xBF, false),
        // Whitespace / editing
        ["Space"] = new(0x20, false), ["Tab"] = new(0x09, false), ["Enter"] = new(0x0D, false),
        ["Backspace"] = new(0x08, false),
        // Modifiers
        ["ShiftLeft"] = new(0x10, false), ["ShiftRight"] = new(0x10, false),
        ["ControlLeft"] = new(0x11, false), ["ControlRight"] = new(0x11, true),
        ["AltLeft"] = new(0x12, false), ["AltRight"] = new(0x12, true),
        ["MetaLeft"] = new(0x5B, true), ["MetaRight"] = new(0x5C, true),
        ["CapsLock"] = new(0x14, false),
        // Navigation (extended set)
        ["ArrowUp"] = new(0x26, true), ["ArrowDown"] = new(0x28, true),
        ["ArrowLeft"] = new(0x25, true), ["ArrowRight"] = new(0x27, true),
        ["Home"] = new(0x24, true), ["End"] = new(0x23, true),
        ["PageUp"] = new(0x21, true), ["PageDown"] = new(0x22, true),
        ["Insert"] = new(0x2D, true), ["Delete"] = new(0x2E, true),
        // Function keys
        ["F1"] = new(0x70, false), ["F2"] = new(0x71, false), ["F3"] = new(0x72, false),
        ["F4"] = new(0x73, false), ["F5"] = new(0x74, false), ["F6"] = new(0x75, false),
        ["F7"] = new(0x76, false), ["F8"] = new(0x77, false), ["F9"] = new(0x78, false),
        ["F10"] = new(0x79, false), ["F11"] = new(0x7A, false), ["F12"] = new(0x7B, false),
        ["F13"] = new(0x7C, false), ["F14"] = new(0x7D, false), ["F15"] = new(0x7E, false),
        ["F16"] = new(0x7F, false), ["F17"] = new(0x80, false), ["F18"] = new(0x81, false),
        ["F19"] = new(0x82, false), ["F20"] = new(0x83, false), ["F21"] = new(0x84, false),
        ["F22"] = new(0x85, false), ["F23"] = new(0x86, false), ["F24"] = new(0x87, false),
        // Numpad
        ["Numpad0"] = new(0x60, false), ["Numpad1"] = new(0x61, false),
        ["Numpad2"] = new(0x62, false), ["Numpad3"] = new(0x63, false),
        ["Numpad4"] = new(0x64, false), ["Numpad5"] = new(0x65, false),
        ["Numpad6"] = new(0x66, false), ["Numpad7"] = new(0x67, false),
        ["Numpad8"] = new(0x68, false), ["Numpad9"] = new(0x69, false),
        ["NumpadMultiply"] = new(0x6A, false), ["NumpadAdd"] = new(0x6B, false),
        ["NumpadSubtract"] = new(0x6D, false), ["NumpadDecimal"] = new(0x6E, false),
        ["NumpadDivide"] = new(0x6F, true), ["NumpadEnter"] = new(0x0D, true),
        ["NumLock"] = new(0x90, true),
        // System
        ["Escape"] = new(0x1B, false), ["PrintScreen"] = new(0x2C, true),
        ["ScrollLock"] = new(0x91, false), ["Pause"] = new(0x13, false),
        ["ContextMenu"] = new(0x5D, true),
    };

    public static bool TryGet(string code, out Entry entry)
    {
        if (string.IsNullOrEmpty(code))
        {
            entry = default;
            return false;
        }
        return Table.TryGetValue(code, out entry);
    }
}
