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
    public void copyText(PluginCall call) {
        String text = call.getString("text");
        if (text == null || text.length() > 200000) { call.reject("Invalid text size."); return; }
        ClipboardManager clipboard = (ClipboardManager)getContext().getSystemService(Context.CLIPBOARD_SERVICE);
        clipboard.setPrimaryClip(ClipData.newPlainText("CipherCraft result", text));
        call.resolve();
    }
}
