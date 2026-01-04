# Smart-Grocery-Box
**Camera-based automatic checkout prototype running entirely on Raspberry Pi**

Smart-Grocery-Box is a local, self-contained automatic checkout system for small grocery or convenience stores, maker spaces, and educational demonstrations. It uses computer vision (Edge Impulse) to detect items placed in view of a USB camera, tracks them in a virtual cart, and displays a real-time checkout interface accessible from any device on the same network.

Unlike cloud-dependent solutions, everything runs **locally** on a Raspberry Pi — no external servers, no Heroku deployment, and no subscription fees. Perfect for students, makers, and anyone exploring IoT + machine learning.

---

## Features

- **Vision-only operation**: No load cell or GPIO required for the MVP
- **Real-time object detection**: Uses Edge Impulse `.eim` model for on-device inference
- **Local API + Web UI**: Node.js/Express backend with a clean HTML/CSS/JS frontend
- **Multi-device access**: View the cart from your phone, tablet, or PC on the same Wi-Fi network
- **Configurable pricing**: Simple JSON file to map product labels to prices
- **Streak-based detection**: Reduces false positives by requiring stable detections over multiple frames
- **Cooldown logic**: Prevents duplicate additions when an item stays in view
- **Extensible**: Easy to add weight sensors, lighting controls, or custom logic

---

## Architecture Overview

```
┌─────────────┐
│ USB Camera  │
└──────┬──────┘
       │ Video feed
       ▼
┌────────────────────────────────────┐
│  billing_vision_only.py            │
│  (Edge Impulse inference)          │
│  - Detects items with confidence   │
│  - Tracks streak & cooldown        │
│  - Reads prices.json               │
└────────┬───────────────────────────┘
         │ HTTP POST /product
         ▼
┌────────────────────────────────────┐
│  CheckoutUI/server/server.js       │
│  (Node.js + Express API)           │
│  - Manages cart (in-memory)        │
│  - Serves static web UI            │
└────────┬───────────────────────────┘
         │ GET /product (polling)
         ▼
┌────────────────────────────────────┐
│  CheckoutUI/client/index.html      │
│  (Web UI)                          │
│  - Displays cart items & total     │
│  - Auto-refreshes every 2s         │
│  - Clear cart button               │
└────────────────────────────────────┘
```

**Data flow:**
1. Camera captures frames → `billing_vision_only.py` runs Edge Impulse model
2. High-confidence detections (≥90% for 8 frames) → POST to local API with product name, price, quantity
3. Web UI polls API → renders cart + total price
4. User can clear cart via UI or checkout (freezes order)

---

## What You Need

### Hardware
- **Raspberry Pi 4** (2GB+ RAM recommended; Pi 3 may work but slower)
- **microSD card** (16GB+, Class 10 or better)
- **USB camera** (UVC-compatible; most webcams work)
- **Power supply** (official 5V 3A USB-C recommended)
- **Wi-Fi** or Ethernet for network access
- *(Optional for future)* Load cell + HX711 ADC for weight-based verification

### Software
- **Raspberry Pi OS** (64-bit, Bookworm or later recommended)
- **Development machine**: Windows 11 with VS Code + Remote-SSH extension
- **On Raspberry Pi**:
  - Python 3.9+ (pre-installed)
  - Node.js 16+ (install via apt)
  - OpenCV (via system package)
  - Edge Impulse Linux SDK (via pip)

---

## Setup Instructions

### 1. Flash Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert your microSD card
3. In Imager, choose:
   - **OS**: Raspberry Pi OS (64-bit) recommended
   - **Storage**: Your microSD card
   - Click ⚙️ (Settings) to:
     - Set hostname: `smartgrocery` (or your choice)
     - Enable SSH (password or key authentication)
     - Configure Wi-Fi: SSID, password, country
     - Set username/password (e.g., `pi` / `yourpassword`)
4. Write the image and wait for completion

### 2. Boot and Find Your Pi

1. Insert the microSD card into the Raspberry Pi
2. Power it on and wait ~60 seconds for first boot
3. From your PC, find the Pi's IP address:
   ```bash
   # Windows (PowerShell)
   ping smartgrocery.local
   
   # Or check your router's DHCP leases
   # Or use a network scanner like Angry IP Scanner
   ```
   Example output: `64 bytes from 192.168.1.42`

### 3. SSH into the Pi

**Option A: Terminal**
```bash
ssh pi@192.168.1.42
# Enter your password when prompted
```

**Option B: VS Code Remote-SSH (Recommended)**
1. Install the **Remote - SSH** extension in VS Code
2. Press `Ctrl+Shift+P` → "Remote-SSH: Connect to Host"
3. Enter: `pi@192.168.1.42`
4. Choose Linux, enter password
5. Open a folder: `/home/pi/Smart-Grocery-Box`

### 4. Copy Project to Pi

From your **Windows PC** (PowerShell or Command Prompt):
```powershell
# If you have a ZIP, extract it first, then:
scp -r C:\Users\YourName\Downloads\Smart-Grocery-Box pi@192.168.1.42:/home/pi/

# Or use WinSCP, FileZilla, or VS Code's drag-and-drop in Remote-SSH
```

### 5. Install System Dependencies

SSH into the Pi (or use VS Code's integrated terminal):
```bash
sudo apt update
sudo apt install -y nodejs npm python3-pip python3-venv python3-opencv

# Verify installations
node --version    # Should be v16.x or higher
python3 --version # Should be 3.9+
```

### 6. Install Node.js Dependencies

```bash
cd ~/Smart-Grocery-Box/CheckoutUI/server
npm install
```

### 7. Install Python Dependencies

```bash
cd ~/Smart-Grocery-Box

# Create virtual environment (--system-site-packages ensures OpenCV is available)
python3 -m venv .venv --system-site-packages

# Activate it
source .venv/bin/activate

# Upgrade pip and install packages
pip install --upgrade pip
pip install edge-impulse-linux requests
```

---

## Running the System

You'll need **two terminal sessions** (or use `tmux`/`screen` for background processes).

### Terminal 1: Start the Backend + Web UI

```bash
cd ~/Smart-Grocery-Box/CheckoutUI/server
node server.js
```

Expected output:
```
Server listening on port 3000!
```

### Terminal 2: Start the Vision Inference

```bash
cd ~/Smart-Grocery-Box
source .venv/bin/activate
python3 billing_vision_only.py modelfile.eim
```

**Optional**: Specify camera index if you have multiple cameras:
```bash
python3 billing_vision_only.py modelfile.eim 0
```

Expected output:
```
[Smart-Grocery-Box] Model: modelfile.eim
[Smart-Grocery-Box] Camera ID: 0
[AutoBill] API URL: http://localhost:3000/product
[AutoBill] threshold=0.90, streak_frames=8, cooldown_s=2.0
[Smart-Grocery-Box] Created prices.json template. Edit it to set real prices.
[AutoBill] Labels: ['apple', 'banana', 'orange']
[AutoBill] apple: 0.342
[AutoBill] banana: 0.891
[AutoBill] banana: 0.923
...
```

### Access the Web UI

From **any device on the same network**:
```
http://192.168.1.42:3000/
```
(Replace `192.168.1.42` with your Pi's actual IP address)

You should see:
- Current cart items with name, price, quantity, and subtotal
- Total payable amount
- "Clear Cart" button

The UI auto-refreshes every 2 seconds to show new items detected by the camera.

---

## Configuration

### `prices.json` — Product Pricing

When you first run `billing_vision_only.py`, it creates a template `prices.json` with all labels from your model set to `1.0`:

```json
{
  "apple": 1.0,
  "banana": 1.0,
  "orange": 1.0
}
```

Edit this file to set real prices (in your local currency):

```json
{
  "apple": 0.5,
  "banana": 0.3,
  "orange": 0.75
}
```

Restart `billing_vision_only.py` after editing.

### Camera Selection

To check available cameras:
```bash
ls /dev/video*
# Example output: /dev/video0  /dev/video1

v4l2-ctl --list-devices
# Shows camera names and their /dev/video paths
```

Specify the camera index as the second argument:
```bash
python3 billing_vision_only.py modelfile.eim 0  # Uses /dev/video0
```

### Environment Variables (Advanced)

The Python script supports optional environment variables:

```bash
export SMART_GROCERY_BOX_API_URL="http://localhost:3000/product"
export SMART_GROCERY_BOX_THRESHOLD=0.90        # Min confidence (0.0 - 1.0)
export SMART_GROCERY_BOX_STREAK_FRAMES=8       # Stable frames required
export SMART_GROCERY_BOX_COOLDOWN_SECONDS=2.0  # Seconds between same item
export SMART_GROCERY_BOX_UNIT="pcs"            # Unit label (pcs, kg, etc.)
export SMART_GROCERY_BOX_PRICES_FILE="prices.json"
```

### Replacing the Model (`modelfile.eim`)

The included `modelfile.eim` is a **demo model** trained on sample objects. For **your own products**:

1. Sign up at [Edge Impulse](https://www.edgeimpulse.com/)
2. Create a new project (Object Detection or Image Classification)
3. Collect and label images of your products
4. Train the model
5. Download the **Linux (AARCH64)** `.eim` file
6. Replace `modelfile.eim` in the project root:
   ```bash
   scp your-new-model.eim pi@192.168.1.42:/home/pi/Smart-Grocery-Box/modelfile.eim
   ```
7. Update `prices.json` with the new labels
8. Restart `billing_vision_only.py`

---

## Troubleshooting

### Web UI Not Loading

**Symptom**: Browser shows "This site can't be reached" or times out  
**Fixes**:
- Confirm the Pi and your device are on the **same Wi-Fi network**
- Verify the server is running: `ps aux | grep node`
- Check the correct IP: `hostname -I` on the Pi
- Try port forwarding if using VPN/firewall
- Access from Pi itself: `curl http://localhost:3000/product` (should return `[]`)

### Camera Not Detected

**Symptom**: "No webcams found" or script fails to start  
**Fixes**:
```bash
# List video devices
ls /dev/video*

# Check USB connections
lsusb

# Test with v4l2-ctl
sudo apt install v4l-utils
v4l2-ctl --list-devices
v4l2-ctl --device=/dev/video0 --all

# Test with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read()[0])"
```

If no camera appears:
- Check USB cable and power
- Try a different USB port
- Some cameras need kernel modules: `sudo modprobe uvcvideo`
- Check `dmesg | grep video` for errors

### Node.js Not Installed or Wrong Version

**Symptom**: `bash: node: command not found` or version < 16  
**Fix**:
```bash
sudo apt update
sudo apt install -y nodejs npm

# If version is too old, use NodeSource repo:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### OpenCV Issues (`cv2` Module Not Found)

**Symptom**: `ModuleNotFoundError: No module named 'cv2'`  
**Fix**:
```bash
# Install system OpenCV
sudo apt install -y python3-opencv

# Ensure venv was created with --system-site-packages
python3 -m venv .venv --system-site-packages
source .venv/bin/activate

# Test
python3 -c "import cv2; print(cv2.__version__)"
```

### Edge Impulse Runner Install Fails

**Symptom**: `pip install edge-impulse-linux` errors  
**Fixes**:
```bash
# Install build dependencies
sudo apt install -y python3-dev build-essential

# Ensure pip is updated
pip install --upgrade pip setuptools wheel

# Retry
pip install edge-impulse-linux
```

Check [Edge Impulse Linux SDK docs](https://docs.edgeimpulse.com/docs/deployment/running-your-impulse-linux) for platform-specific issues.

### Detection Not Triggering

**Symptom**: Camera shows frames but no items added to cart  
**Debugging**:
- Check console output: `[AutoBill] label: score` — is score above 0.90?
- Lower threshold: `export SMART_GROCERY_BOX_THRESHOLD=0.70`
- Reduce streak: `export SMART_GROCERY_BOX_STREAK_FRAMES=3`
- Verify model labels match `prices.json` keys
- Improve lighting and camera angle
- Retrain model with more diverse images

### API Connection Errors

**Symptom**: `[AutoBill] ERROR posting to API: Connection refused`  
**Fixes**:
- Ensure `server.js` is running on port 3000
- Check firewall: `sudo ufw status` (disable for testing: `sudo ufw disable`)
- Verify API URL: `curl http://localhost:3000/product`

---

## API Reference

### Endpoints (CheckoutUI Server)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Serves the web UI (`index.html`) |
| `GET` | `/product` | Returns array of cart items |
| `POST` | `/product` | Adds or updates a product in cart |
| `GET` | `/product/:id` | Get single product by ID |
| `POST` | `/product/:id` | Update product by ID |
| `DELETE` | `/product/:id` | Remove product by ID |
| `POST` | `/checkout` | Freeze cart as order, clear cart |
| `GET` | `/checkout` | List all past orders |

**Example POST `/product` body:**
```json
{
  "id": 1,
  "name": "apple",
  "price": 0.5,
  "unit": "pcs",
  "taken": 3,
  "payable": 1.5
}
```

---

## Roadmap / Next Steps

- [ ] **Train a custom Edge Impulse model** for your specific products (current model is demo-only)
- [ ] **Add load cell + HX711** integration to detect add/remove events and reduce false positives
- [ ] **Improve item tracking logic**: de-duplication, persistent IDs, remove detection
- [ ] **Build a physical enclosure**: box with good lighting, fixed camera angle, and product staging area
- [ ] **Implement LED feedback**: green (added), red (error), idle (blue)
- [ ] **Add persistent storage**: SQLite or JSON file to keep cart across reboots
- [ ] **Multi-user support**: separate carts by session or RFID badge
- [ ] **Payment integration**: mock or real payment gateway for checkout
- [ ] **Web UI enhancements**: product images, barcode scanner, manual add/remove
- [ ] **Dockerize** for easier deployment and updates

---

## License & Credits

**License**: MIT (see [LICENSE](LICENSE) or `package.json`)  
**Author**: Sossey Salmane 
**Adapted by**: Smart-Grocery-Box contributors

**Acknowledgments**:

- [Edge Impulse](https://www.edgeimpulse.com/) for on-device ML tooling
- Raspberry Pi Foundation for the incredible platform

**Important Note**: This repository is a **local, patched MVP** of the original concept, re-engineered to run entirely on a Raspberry Pi without cloud dependencies (Heroku, MongoDB Atlas, etc.). It is intended for educational and prototyping purposes.

---

## Contributing

Pull requests and issues welcome! Please follow these guidelines:
- Test on a real Raspberry Pi 4 before submitting
- Update the README if adding features or changing setup steps
- Keep the "fully local" philosophy: no mandatory cloud services

---

## Support

For questions or issues:
1. Check the [Troubleshooting](#troubleshooting) section
2. Open an issue on GitHub with:
   - Raspberry Pi model and OS version
   - Python/Node versions
   - Full error logs
   - Steps to reproduce

---

**Happy hacking! 🚀🛒**
