param(
    [string]$JavaHome = $env:JAVA_HOME,
    [string]$SdkHome = $env:ANDROID_HOME
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
if (-not $JavaHome) {
    $localJdk = Get-ChildItem -LiteralPath (Join-Path $projectRoot '.venv/android-tools') -Directory -Filter 'jdk-21*' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($localJdk) { $JavaHome = $localJdk.FullName }
}
if (-not $SdkHome) { $SdkHome = Join-Path $env:LOCALAPPDATA 'Android/Sdk' }
if (-not $JavaHome -or -not (Test-Path -LiteralPath (Join-Path $JavaHome 'bin/java.exe'))) {
    throw 'Java 21 is required. Set JAVA_HOME or pass -JavaHome with a Java 21 installation.'
}
if (-not (Test-Path -LiteralPath $SdkHome)) { throw 'Set ANDROID_HOME to an Android SDK with platform 36 installed.' }
$savedJava = $env:JAVA_HOME
$savedSdk = $env:ANDROID_HOME
try {
    $env:JAVA_HOME = $JavaHome
    $env:ANDROID_HOME = $SdkHome
    Push-Location $projectRoot
    try {
        & (Join-Path $projectRoot '.venv/Scripts/python.exe') scripts/build_static.py
        if ($LASTEXITCODE) { throw 'Static build failed.' }
        Push-Location mobile
        try {
            & npm.cmd ci --no-audit --no-fund
            if ($LASTEXITCODE) { throw 'Mobile dependency installation failed.' }
            & .\node_modules\.bin\cap.cmd sync android
            if ($LASTEXITCODE) { throw 'Android asset synchronization failed.' }
            Push-Location android
            try {
                & .\gradlew.bat assembleDebug --no-daemon
                if ($LASTEXITCODE) { throw 'Android APK build failed.' }
            } finally { Pop-Location }
        } finally { Pop-Location }
        $apk = Join-Path $projectRoot 'dist/CipherCraft-android-test.apk'
        Copy-Item -LiteralPath 'mobile/android/app/build/outputs/apk/debug/app-debug.apk' -Destination $apk
        $hash = (Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash.ToLowerInvariant()
        Set-Content -LiteralPath ($apk + '.sha256') -Value ($hash + '  CipherCraft-android-test.apk') -Encoding ascii
        Write-Output $apk
        Write-Output ('SHA256: ' + $hash)
    } finally { Pop-Location }
} finally {
    $env:JAVA_HOME = $savedJava
    $env:ANDROID_HOME = $savedSdk
}
