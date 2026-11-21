import { localDev } from "eve/channels/auth";
import { eveChannel } from "eve/channels/eve";
import { serviceToken } from "../../../../shared/auth";

// Only the SpreadLens engine (service bearer token) may call this agent; localDev() admits the local dev TUI.
export default eveChannel({
  auth: [serviceToken(), localDev()],
});
