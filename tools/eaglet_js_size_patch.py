from pathlib import Path

root = Path("workspace")

# JavaScript TeaVM target: optimize for release and modern browsers
p = root / "target_teavm_javascript/build.gradle.kts"
s = p.read_text()
s = s.replace('implementation(libs.jorbis)\n', '')
s = s.replace('sourceMap = true', 'sourceMap = false')
s = s.replace('optimization = OptimizationLevel.BALANCED // Change to "AGGRESSIVE" for release',
              'optimization = OptimizationLevel.BALANCED')
# Remove the legacy ES6 compatibility shim injection. Eaglet targets modern browsers.
marker = 'tasks.named<GenerateJavaScriptTask>("generateJavaScript") {'
if marker in s:
    a = s.index(marker)
    b = s.index('\neaglercraftBuild {', a)
    s = s[:a] + s[b+1:]
p.write_text(s)

# 1) Remove embedded JOrbis and browser codec-probe fallbacks.
p = root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformAudio.java"
s = p.read_text()
s = s.replace('import net.lax1dude.eaglercraft.v1_8.internal.teavm.JOrbisAudioBufferDecoder;\n', '')

probe_start = s.index('\t\tdetectOGGSupport();')
probe_end = s.index('\n\t\tPlatformInput.clearEventBuffers();', probe_start)
s = s[:probe_start] + '\t\toggSupport = true;\n' + s[probe_end:]

decode_start = s.index('\tprivate static AudioBuffer decodeAudioData(byte[] data, String errorFileName) {')
decode_end = s.index('\n\t@Async\n\tpublic static native AudioBuffer decodeAudioBrowserAsync', decode_start)
decode_replacement = '''\tprivate static AudioBuffer decodeAudioData(byte[] data, String errorFileName) {
\t\tif(data == null) {
\t\t\treturn null;
\t\t}
\t\tInt8Array arr = Int8Array.create(data.length);
\t\tarr.set(TeaVMUtils.unwrapByteArray(data), 0);
\t\treturn decodeAudioBrowserAsync(arr.getBuffer(), errorFileName);
\t}
'''
s = s[:decode_start] + decode_replacement + s[decode_end:]

# Recording is compiled out, so these hot playback paths never need a recording destination.
s = s.replace('''\t\tif(gameRecGain != null) {
\t\t\tgain.connect(gameRecGain);
\t\t}
''', '')
p.write_text(s)

jorbis = root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/teavm/JOrbisAudioBufferDecoder.java"
if jorbis.exists():
    jorbis.unlink()

for name in ("audioctx_test_ogg.dat", "audioctx_test_wav16.dat", "audioctx_test_wav32f.dat"):
    q = root / "desktopRuntime/resources/assets/eagler" / name
    if q.exists():
        q.unlink()

# 2 + 6) Screen recording/video capture off at compile time.
(root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformScreenRecord.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal;

import org.teavm.jso.browser.Window;
import org.teavm.jso.dom.html.HTMLCanvasElement;
import org.teavm.jso.webaudio.MediaStream;

import net.lax1dude.eaglercraft.v1_8.recording.EnumScreenRecordingCodec;

public class PlatformScreenRecord {
    static void initContext(Window win, HTMLCanvasElement canvas) {}
    static void captureFrameHook() {}
    static MediaStream getMic() { return null; }
    static void destroy() {}
    public static boolean isSupported() { return false; }
    public static boolean isCodecSupported(EnumScreenRecordingCodec codec) { return false; }
    public static void setGameVolume(float volume) {}
    public static void setMicrophoneVolume(float volume) {}
    public static void startRecording(ScreenRecordParameters params) {}
    public static void endRecording() {}
    public static boolean isRecording() { return false; }
    public static boolean isMicVolumeLocked() { return false; }
    public static boolean isVSyncLocked() { return false; }
}
''')

# 3) Voice chat off at compile time.
(root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformVoiceClient.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal;

import org.teavm.jso.webaudio.AudioNode;

import net.lax1dude.eaglercraft.v1_8.EaglercraftUUID;
import net.lax1dude.eaglercraft.v1_8.voice.EnumVoiceChannelReadyState;

public class PlatformVoiceClient {
    public static boolean isSupported() { return false; }
    public static void setICEServers(String[] urls) {}
    public static void activateVoice(boolean talk) {}
    public static void initializeDevices() {}
    public static void tickVoiceClient() {}
    public static void setMicVolume(float val) {}
    public static EnumVoiceChannelReadyState getReadyState() { return EnumVoiceChannelReadyState.NONE; }
    public static void signalConnect(EaglercraftUUID peerId, boolean offer) {}
    public static void signalDescription(EaglercraftUUID peerId, String descJSON) {}
    public static void signalDisconnect(EaglercraftUUID peerId, boolean quiet) {}
    public static void makePeerGlobal(EaglercraftUUID peerId) {}
    public static void makePeerProximity(EaglercraftUUID peerId) {}
    public static void setVoiceProximity(int prox) {}
    public static void updateVoicePosition(EaglercraftUUID uuid, double x, double y, double z) {}
    public static void mutePeer(EaglercraftUUID peerId, boolean muted) {}
    public static void signalICECandidate(EaglercraftUUID peerId, String candidate) {}
    public static void setVoiceListenVolume(float f) {}
    static void addRecordingDest(AudioNode destNode) {}
    static void removeRecordingDest(AudioNode destNode) {}
}
''')

# 4) WebRTC/shared-world LAN off; normal websocket multiplayer stays.
(root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformWebRTC.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal;

import java.util.Collections;
import java.util.List;

import org.teavm.jso.typedarrays.ArrayBuffer;

import net.lax1dude.eaglercraft.v1_8.sp.lan.LANPeerEvent;

public class PlatformWebRTC {
    public static boolean supported() { return false; }
    public static void runScheduledTasks() {}
    public static void startRTCLANClient() {}
    public static int clientLANReadyState() { return 0; }
    public static void clientLANCloseConnection() {}
    public static void clientLANSendPacket(byte[] pkt) {}
    public static byte[] clientLANReadPacket() { return null; }
    public static List<byte[]> clientLANReadAllPacket() { return Collections.emptyList(); }
    public static void clientLANSetICEServersAndConnect(String[] servers) {}
    public static void clearLANClientState() {}
    public static String clientLANAwaitICECandidate() { return null; }
    public static String clientLANAwaitDescription() { return null; }
    public static boolean clientLANAwaitChannel() { return false; }
    public static boolean clientLANClosed() { return true; }
    public static void clientLANSetICECandidate(String candidate) {}
    public static void clientLANSetDescription(String description) {}
    public static void startRTCLANServer() {}
    public static void serverLANInitializeServer(String[] servers) {}
    public static void serverLANCloseServer() {}
    public static void serverLANCreatePeer(String peer) {}
    public static LANPeerEvent serverLANGetEvent(String peer) { return null; }
    public static List<LANPeerEvent> serverLANGetAllEvent(String peer) { return Collections.emptyList(); }
    public static void serverLANWritePacket(String peer, byte[] data) {}
    public static void serverLANPeerICECandidates(String peer, String iceCandidates) {}
    public static void serverLANPeerDescription(String peer, String description) {}
    public static void serverLANPeerMapIPC(String peer, String ipcChannel) {}
    public static boolean serverLANPeerPassIPC(String channelName, ArrayBuffer data) { return false; }
    public static void serverLANDisconnectPeer(String peer) {}
    public static int countPeers() { return 0; }
}
''')

# Higher-level recording controller: unreachable/stubbed so TeaVM can DCE its dependencies.
(root / "src/main/java/net/lax1dude/eaglercraft/v1_8/recording/ScreenRecordingController.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.recording;

import java.util.Collections;
import java.util.List;
import java.util.Set;

import net.lax1dude.eaglercraft.v1_8.internal.ScreenRecordParameters;

public class ScreenRecordingController {
    public static final int DEFAULT_FPS = 30;
    public static final int DEFAULT_RESOLUTION = 1;
    public static final int DEFAULT_AUDIO_BITRATE = 120;
    public static final int DEFAULT_VIDEO_BITRATE = 2500;
    public static final float DEFAULT_GAME_VOLUME = 1.0f;
    public static final float DEFAULT_MIC_VOLUME = 0.0f;
    public static final List<EnumScreenRecordingCodec> simpleCodecsOrdered = Collections.emptyList();
    public static final List<EnumScreenRecordingCodec> advancedCodecsOrdered = Collections.emptyList();
    public static final Set<EnumScreenRecordingCodec> codecs = Collections.emptySet();
    public static void initialize() {}
    public static boolean isSupported() { return false; }
    public static void setGameVolume(float volume) {}
    public static void setMicrophoneVolume(float volume) {}
    public static void startRecording(ScreenRecordParameters params) {}
    public static void endRecording() {}
    public static boolean isRecording() { return false; }
    public static boolean isMicVolumeLocked() { return false; }
    public static boolean isVSyncLocked() { return false; }
    public static EnumScreenRecordingCodec getDefaultCodec() { return null; }
}
''')

# Higher-level voice controller: preserve protocol-facing API but never activate voice.
(root / "src/main/java/net/lax1dude/eaglercraft/v1_8/voice/VoiceClientController.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.voice;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

import net.lax1dude.eaglercraft.v1_8.EaglercraftUUID;
import net.lax1dude.eaglercraft.v1_8.socket.protocol.pkt.GameMessagePacket;
import net.lax1dude.eaglercraft.v1_8.socket.protocol.pkt.server.SPacketVoiceSignalGlobalEAG;

public class VoiceClientController {
    static EnumVoiceChannelType lastVoiceChannel = EnumVoiceChannelType.NONE;
    public static boolean isSupported() { return false; }
    public static boolean isClientSupported() { return false; }
    public static boolean isServerSupported() { return false; }
    public static void initializeVoiceClient(Consumer<GameMessagePacket> cb, int proto) {}
    public static void handleVoiceSignalPacketTypeGlobalNew(Collection<SPacketVoiceSignalGlobalEAG.UserData> p) {}
    public static void handleServerDisconnect() {}
    public static void handleVoiceSignalPacketTypeAllowed(boolean stat, String[] servs) {}
    public static void handleVoiceSignalPacketTypeConnect(EaglercraftUUID user, boolean offer) {}
    public static void handleVoiceSignalPacketTypeConnectAnnounce(EaglercraftUUID user) {}
    public static void handleVoiceSignalPacketTypeDisconnect(EaglercraftUUID user) {}
    public static void handleVoiceSignalPacketTypeICECandidate(EaglercraftUUID user, String ice) {}
    public static void handleVoiceSignalPacketTypeDescription(EaglercraftUUID user, String desc) {}
    public static void tickVoiceClient() {}
    public static void setVoiceChannel(EnumVoiceChannelType channel) { lastVoiceChannel = EnumVoiceChannelType.NONE; }
    public static EnumVoiceChannelType getVoiceChannel() { return EnumVoiceChannelType.NONE; }
    public static EnumVoiceChannelStatus getVoiceStatus() { return EnumVoiceChannelStatus.UNAVAILABLE; }
    public static void activateVoice(boolean talk) {}
    public static void setVoiceProximity(int prox) {}
    public static int getVoiceProximity() { return 16; }
    public static void setVoiceListenVolume(float f) {}
    public static float getVoiceListenVolume() { return 0.5f; }
    public static void setVoiceSpeakVolume(float f) {}
    public static float getVoiceSpeakVolume() { return 0.5f; }
    public static Set<EaglercraftUUID> getVoiceListening() { return Collections.emptySet(); }
    public static Set<EaglercraftUUID> getVoiceSpeaking() { return Collections.emptySet(); }
    public static void setVoiceMuted(EaglercraftUUID uuid, boolean mute) {}
    public static Set<EaglercraftUUID> getVoiceMuted() { return Collections.emptySet(); }
    public static List<EaglercraftUUID> getVoiceRecent() { return Collections.emptyList(); }
    public static String getVoiceUsername(EaglercraftUUID uuid) { return uuid.toString(); }
    public static void sendPacketICE(EaglercraftUUID peerId, String candidate) {}
    public static void sendPacketDesc(EaglercraftUUID peerId, String desc) {}
    public static void sendPacketDisconnectPeer(EaglercraftUUID peerId) {}
}
''')

# Shared-world controller stub. Singleplayer itself is retained.
(root / "src/main/java/net/lax1dude/eaglercraft/v1_8/sp/lan/LANServerController.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.sp.lan;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

import net.lax1dude.eaglercraft.v1_8.sp.relay.RelayServerSocket;

public class LANServerController {
    public static final List<String> currentICEServers = new ArrayList<>();
    static RelayServerSocket lanRelaySocket = null;
    public static String shareToLAN(Consumer<String> progressCallback, String worldName, boolean worldHidden) { return null; }
    public static String getCurrentURI() { return "<disconnected>"; }
    public static String getCurrentCode() { return "<undefined>"; }
    public static void closeLAN() {}
    public static void closeLANNoKick() {}
    public static void cleanupLAN() {}
    public static boolean hasPeers() { return false; }
    public static boolean isHostingLAN() { return false; }
    public static boolean isLANOpen() { return false; }
    public static void updateLANServer() {}
    public static boolean supported() { return false; }
}
''')


# --- Ultra JS-only cuts: direct launcher, no boot menu/update UI/debug popup/crash UI ---

# Hard-disable optional launcher/update features in the JS config adapter so TeaVM can fold callers.
p = root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/teavm/TeaVMClientConfigAdapter.java"
s = p.read_text()
s = s.replace('public boolean isShowBootMenuOnLaunch() {\n\t\treturn showBootMenuOnLaunch;\n\t}',
              'public boolean isShowBootMenuOnLaunch() {\n\t\treturn false;\n\t}')
s = s.replace('public boolean isBootMenuBlocksUnsignedClients() {\n\t\treturn bootMenuBlocksUnsignedClients;\n\t}',
              'public boolean isBootMenuBlocksUnsignedClients() {\n\t\treturn false;\n\t}')
s = s.replace('public boolean isAllowBootMenu() {\n\t\treturn allowBootMenu;\n\t}',
              'public boolean isAllowBootMenu() {\n\t\treturn false;\n\t}')
s = s.replace('public boolean allowUpdateSvc() {\n\t\treturn isAllowUpdateSvc;\n\t}',
              'public boolean allowUpdateSvc() {\n\t\treturn false;\n\t}')
s = s.replace('public boolean allowUpdateDL() {\n\t\treturn isAllowUpdateDL;\n\t}',
              'public boolean allowUpdateDL() {\n\t\treturn false;\n\t}')
s = s.replace('public boolean isEnableDownloadOfflineButton() {\n\t\treturn isEnableDownloadOfflineButton;\n\t}',
              'public boolean isEnableDownloadOfflineButton() {\n\t\treturn false;\n\t}')
s = s.replace('public boolean isAllowVoiceClient() {\n\t\treturn allowVoiceClient;\n\t}',
              'public boolean isAllowVoiceClient() {\n\t\treturn false;\n\t}')
p.write_text(s)

# Signed-client updater/installer is not needed by the standalone Eaglet build.
(root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformUpdateSvc.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal;

import net.lax1dude.eaglercraft.v1_8.update.UpdateCertificate;
import net.lax1dude.eaglercraft.v1_8.update.UpdateProgressStruct;
import net.lax1dude.eaglercraft.v1_8.update.UpdateResultObj;

public class PlatformUpdateSvc {
    public static Thread updateThread = null;
    private static final UpdateProgressStruct progressStruct = new UpdateProgressStruct();
    public static boolean supported() { return false; }
    public static void initialize() {}
    public static byte[] getClientSignatureData() { return null; }
    public static byte[] getClientBundleData() { return null; }
    public static void startClientUpdateFrom(UpdateCertificate clientUpdate) {}
    public static UpdateProgressStruct getUpdatingStatus() { return progressStruct; }
    public static UpdateResultObj getUpdateResult() { return null; }
    public static void setUpdateResultTeaVM(UpdateResultObj obj) {}
    public static void installSignedClient(UpdateCertificate clientCert, byte[] clientPayload, boolean setDefault, boolean setTimeout) {}
    public static void quine(String filename, byte[] cert, byte[] data, String date) {}
    public static void quine(UpdateCertificate clientUpdate, byte[] data) {}
}
''')

# Debug console popup is optional and keeps a lot of DOM/log buffering code reachable.
(root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/teavm/DebugConsoleWindow.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal.teavm;

import org.teavm.jso.browser.Window;

public class DebugConsoleWindow {
    public static Window parent = null;
    public static Window logger = null;
    public static void initialize(Window parentWindow) { parent = parentWindow; }
    public static void removeEventListeners() {}
    public static void showDebugConsole() {}
    public static void addLogMessage(String text, boolean isErr) {}
    public static void destroyWindow() {}
    public static boolean isShowingDebugConsole() { return false; }
}
''')

# Replace the huge generic launcher/crash UI with the tiny direct Eaglet launcher.
(root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/teavm/ClientMain.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal.teavm;

import org.teavm.jso.JSBody;
import org.teavm.jso.JSObject;
import org.teavm.jso.browser.Window;
import org.teavm.jso.dom.html.HTMLElement;

import net.lax1dude.eaglercraft.v1_8.EagRuntime;
import net.lax1dude.eaglercraft.v1_8.internal.teavm.opts.JSEaglercraftXOptsRoot;
import net.minecraft.client.main.Main;

public class ClientMain {

    @JSBody(script = "return (typeof eaglercraftXOpts === \\"undefined\\") ? null : (typeof eaglercraftXOpts === \\"string\\" ? JSON.parse(eaglercraftXOpts) : eaglercraftXOpts);")
    private static native JSObject getEaglerXOpts();

    public static void _main() {
        JSObject raw = getEaglerXOpts();
        if(raw == null) {
            throw new RuntimeException("eaglercraftXOpts is undefined");
        }
        JSEaglercraftXOptsRoot opts = (JSEaglercraftXOptsRoot)raw;
        configRootElementId = opts.getContainer();
        String assets = opts.getAssetsURI();
        if(configRootElementId == null || assets == null) {
            throw new RuntimeException("container/assetsURI missing");
        }
        configEPKFiles = new EPKFileEntry[] { new EPKFileEntry(assets, "") };
        configLocalesFolder = "lang";
        ((TeaVMClientConfigAdapter)TeaVMClientConfigAdapter.instance).loadNative(opts);
        EagRuntime.create();
        Main.appMain();
    }

    public static class EPKFileEntry {
        public final String url;
        public final String path;
        public EPKFileEntry(String url, String path) {
            this.url = url;
            this.path = path;
        }
    }

    public static String configRootElementId = null;
    public static HTMLElement configRootElement = null;
    public static EPKFileEntry[] configEPKFiles = null;
    public static String configLocalesFolder = "lang";

    public static HTMLElement integratedServerCrashPanel = null;
    public static boolean integratedServerCrashPanelShowing = false;

    public static void showIntegratedServerCrashReportOverlay(String report, int x, int y, int w, int h) {}
    public static void hideIntegratedServerCrashReportOverlay() { integratedServerCrashPanelShowing = false; }

    public static void removeErrorHandler(Window win) {}
    public static void showCrashScreen(String message) {}
    public static void showCrashScreen(String message, Throwable t) {}
    public static void showIncompatibleScreen(String message) {}
    public static void showContextLostScreen(String message) {}
}
''')

# Platform runtime: remove modern-browser compatibility diagnostics, debug popup init,
# boot-menu checks, and the old WebM duration shim call.
p = root / "src/teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformRuntime.java"
s = p.read_text()
s = s.replace('\t\tDebugConsoleWindow.initialize(win);\n', '')
s = s.replace('\t\tboolean allowBootMenu = teavmCfg.isAllowBootMenu();\n', '\t\tboolean allowBootMenu = false;\n')
s = s.replace('\t\tFixWebMDurationJS.checkOldScriptStillLoaded();\n', '')
start = s.find('\t\tES6ShimStatus shimStatus = ES6ShimStatus.getRuntimeStatus();')
end = s.find('\t\tTeaVMBlobURLManager.initialize();', start)
if start != -1 and end != -1:
    s = s[:start] + '\t\tTeaVMBlobURLManager.initialize();\n' + s[end + len('\t\tTeaVMBlobURLManager.initialize();\n'):]
boot_block = '''\t\tif(allowBootMenu && BootMenuEntryPoint.checkShouldLaunchFlag(win)) {
\t\t\tlogger.info("Boot menu enable flag is set, entering boot menu...");
\t\t\tenterBootMenu(BootMenuEntryPoint.wasManuallyInvoked);
\t\t}

'''
s = s.replace(boot_block, '')
s = s.replace('''\t\tif(allowBootMenu) {
\t\t\tcheckBootMenu();
\t\t}

''', '')
p.write_text(s)
