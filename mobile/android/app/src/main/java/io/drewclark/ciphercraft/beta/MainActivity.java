package io.drewclark.ciphercraft.beta;

import com.getcapacitor.BridgeActivity;
import android.os.Bundle;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(CipherFilesPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
