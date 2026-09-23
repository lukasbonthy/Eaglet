from pathlib import Path

root = Path("workspace")

# Build config
p = root / "target_teavm_wasm_gc/build.gradle.kts"
s = p.read_text()
s = s.replace('implementation(libs.jorbis)\n', '')
s = s.replace('debugInformation = true', 'debugInformation = false')
s = s.replace('disassembly = true', 'disassembly = false')
p.write_text(s)

# 1) Remove embedded JOrbis fallback
p = root / "src/wasm-gc-teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformAudio.java"
s = p.read_text()
s = s.replace('import net.lax1dude.eaglercraft.v1_8.internal.wasm_gc_teavm.JOrbisAudioBufferDecoder;\n', '')
s = s.replace('\tprivate static boolean oggSupport = false;\n', '')

init_start = s.index('\tstatic void initialize() {')
get_ctx = s.index('\n\t@Import(module = "platformAudio", name = "getContext")', init_start)
replacement = '''\tstatic void initialize() {
\t\taudioctx = getContext();
\t\tif(audioctx == null) {
\t\t\tlogger.error("Could not initialize audio context!");
\t\t\treturn;
\t\t}

\t\tif(((WASMGCClientConfigAdapter)PlatformRuntime.getClientConfigAdapter()).isKeepAliveHackTeaVM()) {
\t\t\tbyte[] silenceFile = PlatformAssets.getResourceBytes("/assets/eagler/silence_loop.wav");
\t\t\tif (silenceFile != null) {
\t\t\t\tMemoryStack.push();
\t\t\t\ttry {
\t\t\t\t\tint len = silenceFile.length;
\t\t\t\t\tAddress addr = MemoryStack.malloc(len);
\t\t\t\t\tWASMGCDirectArrayCopy.memcpy(addr, silenceFile, 0, len);
\t\t\t\t\tinitKeepAliveHack(addr, len);
\t\t\t\t}finally {
\t\t\t\t\tMemoryStack.pop();
\t\t\t\t}
\t\t\t}
\t\t}
\t}
'''
s = s[:init_start] + replacement + s[get_ctx:]

dec_start = s.index('\tprivate static AudioBuffer decodeAudioData(byte[] data, String errorFileName) {')
dec_end = s.index('\n\t@Import(module = "platformAudio", name = "decodeAudioBrowser")', dec_start)
replacement = '''\tprivate static AudioBuffer decodeAudioData(byte[] data, String errorFileName) {
\t\tif(data == null) {
\t\t\treturn null;
\t\t}
\t\tMemoryStack.push();
\t\ttry {
\t\t\treturn decodeAudioBrowserAsync(WASMGCDirectArrayConverter.byteArrayToStackU8Array(data),
\t\t\t\t\tBetterJSStringConverter.stringToJS(errorFileName));
\t\t}finally {
\t\t\tMemoryStack.pop();
\t\t}
\t}
'''
s = s[:dec_start] + replacement + s[dec_end:]
p.write_text(s)

jorbis_src = root / "src/wasm-gc-teavm/java/net/lax1dude/eaglercraft/v1_8/internal/wasm_gc_teavm/JOrbisAudioBufferDecoder.java"
if jorbis_src.exists():
    jorbis_src.unlink()

# 2 + 6) Compile out screen recording/video encoding
(root / "src/wasm-gc-teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformScreenRecord.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal;

import net.lax1dude.eaglercraft.v1_8.recording.EnumScreenRecordingCodec;

public class PlatformScreenRecord {
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

# 3) Compile out voice chat
(root / "src/wasm-gc-teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformVoiceClient.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal;

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
}
''')

# 4) Remove WebRTC LAN/shared-world transport, keep regular WebSocket multiplayer
(root / "src/wasm-gc-teavm/java/net/lax1dude/eaglercraft/v1_8/internal/PlatformWebRTC.java").write_text(
'''package net.lax1dude.eaglercraft.v1_8.internal;

import java.util.Collections;
import java.util.List;

import net.lax1dude.eaglercraft.v1_8.sp.lan.LANPeerEvent;

public class PlatformWebRTC {
    public static void initialize() {}
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
    public static void serverLANDisconnectPeer(String peer) {}
    public static int countPeers() { return 0; }
}
''')

# Tiny JS no-op implementations so the runtime initializer still has the symbols it expects.
(root / "src/wasm-gc-teavm/js/platformScreenRecord.js").write_text(
'''const platfScreenRecordName = "platformScreenRecord";
function initializePlatfScreenRecord(screenRecordImports) {}
function initializeNoPlatfScreenRecord(screenRecordImports) {}
''')

(root / "src/wasm-gc-teavm/js/platformVoiceClient.js").write_text(
'''const platfVoiceClientName = "platformVoiceClient";
function initializePlatfVoiceClient(voiceClientImports) {}
function initializeNoPlatfVoiceClient(voiceClientImports) {}
''')

(root / "src/wasm-gc-teavm/js/platformWebRTC.js").write_text(
'''const platfWebRTCName = "platformWebRTC";
function initializePlatfWebRTC(webrtcImports) { serverLANPeerPassIPCFunc = null; }
function initializeNoPlatfWebRTC(webrtcImports) { serverLANPeerPassIPCFunc = null; }
''')

(root / "src/wasm-gc-teavm/js/fix-webm-duration.js").write_text('')

ogg_probe = root / "desktopRuntime/resources/assets/eagler/audioctx_test_ogg.dat"
if ogg_probe.exists():
    ogg_probe.unlink()
