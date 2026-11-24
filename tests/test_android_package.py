"""Android must ship its own engine and save through a scoped system picker."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ANDROID = '{http://schemas.android.com/apk/res/android}'


def test_android_configuration_uses_bundled_assets_not_live_site():
    config = json.loads((ROOT / 'mobile/capacitor.config.json').read_text())
    assert config['appId'] == 'io.drewclark.ciphercraft.beta'
    assert config['webDir'] == '../dist/static'
    assert 'url' not in config['server']
    assert config['server']['androidScheme'] == 'https'


def test_android_has_no_internet_or_broad_storage_permission():
    tree = ET.parse(ROOT / 'mobile/android/app/src/main/AndroidManifest.xml')
    permissions = {node.get(ANDROID + 'name') for node in tree.findall('uses-permission')}
    assert not permissions & {'android.permission.INTERNET', 'android.permission.READ_EXTERNAL_STORAGE',
                              'android.permission.WRITE_EXTERNAL_STORAGE', 'android.permission.MANAGE_EXTERNAL_STORAGE'}
    assert tree.find('application').get(ANDROID + 'allowBackup') == 'false'


def test_native_save_uses_document_picker_and_utf8():
    source = (ROOT / 'mobile/android/app/src/main/java/io/drewclark/ciphercraft/beta/CipherFilesPlugin.java').read_text()
    assert 'Intent.ACTION_CREATE_DOCUMENT' in source
    assert 'StandardCharsets.UTF_8' in source
    assert 'getContentResolver().openOutputStream' in source
