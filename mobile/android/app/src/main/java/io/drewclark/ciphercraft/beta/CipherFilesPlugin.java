package io.drewclark.ciphercraft.beta;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;

@CapacitorPlugin(name = "CipherFiles")
public class CipherFilesPlugin extends Plugin {
    private String pendingMessage;

    private String sharedText(Intent intent) {
        if (intent == null || !Intent.ACTION_SEND.equals(intent.getAction()) || !"text/plain".equals(intent.getType())) return null;
        CharSequence extra = intent.getCharSequenceExtra(Intent.EXTRA_TEXT);
        intent.removeExtra(Intent.EXTRA_TEXT);
        if (extra == null) return null;
        if (extra.length() > 4096) return "[Message too large]";
        return extra.toString();
    }

    @Override
    public void load() { pendingMessage = sharedText(getActivity().getIntent()); }

    @Override
    protected void handleOnNewIntent(Intent intent) {
        String text = sharedText(intent);
        if (text != null) notifyListeners("messageReceived", new JSObject().put("text", text), true);
    }

    @PluginMethod
    public void takeSharedMessage(PluginCall call) {
        String text = pendingMessage;
        pendingMessage = null;
        call.resolve(new JSObject().put("text", text == null ? "" : text));
    }

    @PluginMethod
    public void saveText(PluginCall call) {
        String text = call.getString("text");
        String name = call.getString("filename", "message.txt");
        if (text == null || text.length() > 200000) {
            call.reject("Invalid text size.");
            return;
        }
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TITLE, name.replaceAll("[^a-zA-Z0-9_.-]", "_"));
        startActivityForResult(call, intent, "onSave");
    }

    @ActivityCallback
    private void onSave(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null) {
            call.resolve(new JSObject().put("cancelled", true));
            return;
        }
        Uri uri = result.getData().getData();
        if (uri == null) { call.reject("No save location selected."); return; }
        try (OutputStream stream = getContext().getContentResolver().openOutputStream(uri, "wt")) {
            if (stream == null) throw new java.io.IOException("Unable to open destination.");
            stream.write(call.getString("text", "").getBytes(StandardCharsets.UTF_8));
            call.resolve(new JSObject().put("cancelled", false));
        } catch (Exception error) {
            call.reject("Unable to save text.", error);
        }
    }

    @PluginMethod
    public void shareText(PluginCall call) {
        String text = call.getString("text");
        if (text == null || text.length() > 4096) { call.reject("Invalid message size."); return; }
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TEXT, text);
        try {
            getActivity().startActivity(Intent.createChooser(intent, "Share encrypted message"));
            call.resolve();
        } catch (Exception error) { call.reject("Unable to open sharing.", error); }
    }

    @PluginMethod
    public void copyText(PluginCall call) {
        String text = call.getString("text");
        if (text == null || text.length() > 200000) { call.reject("Invalid text size."); return; }
        ClipboardManager clipboard = (ClipboardManager)getContext().getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip = ClipData.newPlainText("CipherCraft result", text);
        if (Boolean.TRUE.equals(call.getBoolean("sensitive", false))) {
            android.os.PersistableBundle extras = new android.os.PersistableBundle();
            extras.putBoolean("android.content.extra.IS_SENSITIVE", true);
            clip.getDescription().setExtras(extras);
        }
        clipboard.setPrimaryClip(clip);
        call.resolve();
    }
}
