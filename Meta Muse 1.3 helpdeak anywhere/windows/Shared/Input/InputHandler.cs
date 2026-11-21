
using System.Text.Json;

namespace HelpdeskAnywhere.Shared.Input;

// Dispatches inbound agent.input messages to the injector. Tracks held
// modifiers and mouse buttons so a drop mid-drag can never leave a stuck
// Ctrl or mouse button on the user's machine (ReleaseAll on session end).
public sealed class InputHandler
{
    private readonly InputInjector _injector = new();
    private readonly HashSet<string> _heldModifiers = new(StringComparer.Ordinal);
    private readonly HashSet<string> _heldButtons = new(StringComparer.Ordinal);
    private readonly Action<string>? _logger;

    public InputHandler(Action<string>? logger = null)
    {
        _logger = logger;
    }

    public void OnAgentInput(string json)
    {
        string kind;
        try
        {
            using JsonDocument doc = JsonDocument.Parse(json);
            JsonElement root = doc.RootElement;
            if (!root.TryGetProperty("kind", out JsonElement kindEl)) return;
            kind = kindEl.GetString() ?? "";
            switch (kind)
            {
                case "mouse-move":
                    _injector.MoveTo(GetInt(root, "x"), GetInt(root, "y"));
                    break;
                case "mouse-down": {
                    string button = GetString(root, "button", "left");
                    _injector.MouseDown(button, GetInt(root, "x"), GetInt(root, "y"));
                    _heldButtons.Add(button);
                    break;
                }
                case "mouse-up": {
                    string button = GetString(root, "button", "left");
                    _injector.MouseUp(button, GetInt(root, "x"), GetInt(root, "y"));
                    _heldButtons.Remove(button);
                    break;
                }
                case "wheel":
                    _injector.Wheel(GetInt(root, "dx"), GetInt(root, "dy"));
                    break;
                case "key-down": {
                    string code = GetString(root, "code", "");
                    _injector.KeyDown(code);
                    if (KeyMap.IsModifier(code)) _heldModifiers.Add(code);
                    break;
                }
                case "key-up": {
                    string code = GetString(root, "code", "");
                    _injector.KeyUp(code);
                    _heldModifiers.Remove(code);
                    break;
                }
                default:
                    return; // unknown kinds are ignored, never crash the session
            }
        }
        catch (JsonException)
        {
            return;
        }
        // Test-only receipt log (never key contents beyond the physical code).
        try
        {
            _logger?.Invoke($"input: {kind}");
        }
        catch
        {
            // logging never breaks input
        }
    }

    public void ReleaseAll()
    {
        foreach (string code in _heldModifiers.ToArray())
        {
            try
            {
                _injector.KeyUp(code);
            }
            catch
            {
                // release path never throws
            }
        }
        _heldModifiers.Clear();
        foreach (string button in _heldButtons.ToArray())
        {
            try
            {
                _injector.MouseUp(button, 0, 0);
            }
            catch
            {
                // release path never throws
            }
        }
        _heldButtons.Clear();
    }

    private static int GetInt(JsonElement root, string name)
    {
        if (root.TryGetProperty(name, out JsonElement el) && el.TryGetInt32(out int v))
        {
            return Math.Clamp(v, -32768, 32767);
        }
        return 0;
    }

    private static string GetString(JsonElement root, string name, string fallback)
    {
        if (root.TryGetProperty(name, out JsonElement el) && el.ValueKind == JsonValueKind.String)
        {
            return el.GetString() ?? fallback;
        }
        return fallback;
    }
}
