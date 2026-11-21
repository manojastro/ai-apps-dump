// Mirrors shared/protocol.md and server/src/protocol.ts.
// Change all three together.
namespace HelpdeskAnywhere.Shared;

public static class Protocol
{
    public const string Version = "1.0.0-phase1";

    public static class MessageTypes
    {
        public const string AgentCreate = "agent.create";
        public const string AgentInput = "agent.input";
        public const string AgentExec = "agent.exec";
        public const string AgentRequestElevation = "agent.requestElevation";
        public const string AgentSas = "agent.sas";
        public const string AgentEnd = "agent.end";
        public const string SessionCreated = "session.created";
        public const string HostJoin = "host.join";
        public const string HostConsent = "host.consent";
        public const string HostDesktopChanged = "host.desktopChanged";
        public const string HostElevated = "host.elevated";
        public const string HostExecResult = "host.execResult";
        public const string HostConnectRequest = "host.connectRequest";
        public const string ConsentResult = "consent.result";
        public const string PeerJoined = "peer.joined";
        public const string PeerLeft = "peer.left";
        public const string Error = "error";
    }

    public static class SessionStates
    {
        public const string WaitingForHost = "waiting_for_host";
        public const string WaitingForConsent = "waiting_for_consent";
        public const string Active = "active";
        public const string Ended = "ended";
    }

    public static class Desktops
    {
        public const string Default = "Default";
        public const string Winlogon = "Winlogon";
        public const string ScreenSaver = "Screen-saver";
    }

    public static class InputKinds
    {
        public const string MouseMove = "mouse-move";
        public const string MouseDown = "mouse-down";
        public const string MouseUp = "mouse-up";
        public const string Wheel = "wheel";
        public const string KeyDown = "key-down";
        public const string KeyUp = "key-up";
    }

    public const byte FrameFull = 0x01;
    public const byte FrameDirty = 0x02;
}
