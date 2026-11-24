package io.drewclark.ciphercraft.beta;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.provider.Settings;
import androidx.core.app.NotificationManagerCompat;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.util.UUID;

@CapacitorPlugin(name = "CipherPush")
public class CipherPushPlugin extends Plugin {
    private SharedPreferences preferences;
    private JSObject pending;

    private JSObject notification(Intent intent) {
        if (intent == null || !intent.hasExtra("google.message_id")) return null;
        String conversation = intent.getStringExtra("conversationId");
        String recipient = intent.getStringExtra("recipientId");
        String message = intent.getStringExtra("messageId");
        if (conversation == null || recipient == null || message == null ||
            !conversation.matches("[1-9][0-9]{0,17}") || !recipient.matches("[1-9][0-9]{0,17}") ||
            !message.matches("[1-9][0-9]{0,17}")) return null;
        intent.removeExtra("google.message_id");
        return new JSObject().put("conversationId", conversation).put("recipientId", recipient).put("messageId", message);
    }

    @Override public void load() {
        preferences = getContext().getSharedPreferences("ciphercraft_push", 0);
        if (!preferences.contains("installationId")) {
            preferences.edit().putString("installationId", UUID.randomUUID().toString()).apply();
        }
        pending = notification(getActivity().getIntent());
    }

    @Override protected void handleOnNewIntent(Intent intent) {
        JSObject value = notification(intent);
        if (value != null) notifyListeners("messageNotificationOpened", value, true);
    }

    @PluginMethod public void getStatus(PluginCall call) {
        boolean configured = getContext().getResources().getIdentifier("google_app_id", "string", getContext().getPackageName()) != 0;
        call.resolve(new JSObject().put("configured", configured)
            .put("installationId", preferences.getString("installationId", ""))
            .put("enabled", preferences.getBoolean("enabled", false))
            .put("notificationsEnabled", NotificationManagerCompat.from(getContext()).areNotificationsEnabled()));
    }

    @PluginMethod public void setEnabled(PluginCall call) {
        preferences.edit().putBoolean("enabled", Boolean.TRUE.equals(call.getBoolean("enabled", false))).apply();
        call.resolve();
    }

    @PluginMethod public void takeLaunchNotification(PluginCall call) {
        JSObject result = pending == null ? new JSObject() : pending;
        pending = null;
        call.resolve(result);
    }

    @PluginMethod public void openSettings(PluginCall call) {
        Intent intent = new Intent(Build.VERSION.SDK_INT >= 26 ? Settings.ACTION_APP_NOTIFICATION_SETTINGS : Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
        if (Build.VERSION.SDK_INT >= 26) intent.putExtra(Settings.EXTRA_APP_PACKAGE, getContext().getPackageName());
        else intent.setData(android.net.Uri.parse("package:" + getContext().getPackageName()));
        getActivity().startActivity(intent);
        call.resolve();
    }
}
