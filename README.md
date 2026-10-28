# iPhone Teleport

Fake your iPhone's GPS location from a Windows PC over a USB cable.

## One-time setup

1. Install **Python** from python.org. During install, tick **"Add python.exe to PATH"**.
2. Install **iTunes** or the **Apple Devices** app from the Microsoft Store. This installs the USB driver Windows needs to see your iPhone.
3. Double-click **install.bat**.
4. Plug in your iPhone, unlock it, and tap **Trust** when it asks.
5. Turn on **Developer Mode** on the iPhone: Settings > Privacy & Security > Developer Mode. If you don't see it, open the app and click **"Show Developer Mode on phone"**, then check again. The phone will restart; confirm after it boots.

## Using it

1. Double-click **run.bat** and click **Yes** on the admin prompt (needed for the iOS 17+ connection).
2. Click **Connect iPhone**.
3. Click a spot on the map, or search for a place, or type coordinates.
4. Click **Teleport**.
5. Click **Back to real location** when you're done.

On iOS 17 and newer, keep the app open and the cable plugged in. The fake location
stops when you close the app or unplug. Restarting the iPhone always restores the real location.

## If something goes wrong

- **install.bat says "Microsoft Visual C++ 14.0 or greater is required"**: install the free Microsoft C++ Build Tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/. In the installer, tick **"Desktop development with C++"**, click Install, restart the PC, then run install.bat again.

- **"No iPhone found"**: unlock the phone, re-plug the cable, check you tapped Trust, and make sure iTunes / Apple Devices is installed.
- **Developer Mode errors**: see setup step 5.
- **Teleport fails on iOS 17+**: close the app, re-open it, and connect again.
- Keep pymobiledevice3 updated (run install.bat again) when you update iOS.

Heads up: some apps (especially games like Pokémon GO) detect location spoofing and can ban accounts.
