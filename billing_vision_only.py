#!/usr/bin/env python3
"""Smart-Grocery-Box (Vision-only) for Raspberry Pi + USB camera.

- Runs Edge Impulse Linux image runner on your camera feed
- When a class is detected with high confidence for several frames,
  it adds/increments the item in the cart via the local CheckoutUI API.

This version DOES NOT require HX711 / load-cell / GPIO.

Environment variables (optional):
- SMART_GROCERY_BOX_API_URL: default "http://localhost:3000/product"
- SMART_GROCERY_BOX_THRESHOLD: default 0.90
- SMART_GROCERY_BOX_STREAK_FRAMES: default 8
- SMART_GROCERY_BOX_COOLDOWN_SECONDS: default 2.0
- SMART_GROCERY_BOX_UNIT: default "pcs"
- SMART_GROCERY_BOX_PRICES_FILE: default "prices.json" (label -> price)

Usage:
  python3 billing_vision_only.py modelfile.eim [camera_id]
"""

import os
import sys
import time
import json
from typing import Dict, Any

import cv2
import requests
from edge_impulse_linux.image import ImageImpulseRunner


def now_ms() -> int:
    return round(time.time() * 1000)


def get_webcams(max_ports: int = 5):
    port_ids = []
    for port in range(max_ports):
        cap = cv2.VideoCapture(port)
        if cap is None or not cap.isOpened():
            continue
        ok, _ = cap.read()
        if ok:
            port_ids.append(port)
        cap.release()
    return port_ids


def load_prices(labels):
    prices_file = os.environ.get("SMART_GROCERY_BOX_PRICES_FILE", "prices.json")
    # Default example mapping — edit prices.json for your products
    default_prices = {label: 1.0 for label in labels}
    if os.path.exists(prices_file):
        try:
            with open(prices_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            # keep only known labels; allow extra keys (ignored)
            for k, v in data.items():
                if k in default_prices:
                    default_prices[k] = float(v)
            print(f"[Smart-Grocery-Box] Loaded prices from {prices_file}")
        except Exception as e:
            print(f"[Smart-Grocery-Box] Could not read {prices_file}: {e}. Using defaults.")
    else:
        # write a template prices.json for convenience
        try:
            with open(prices_file, "w", encoding="utf-8") as f:
                json.dump(default_prices, f, indent=2)
            print(f"[Smart-Grocery-Box] Created {prices_file} template. Edit it to set real prices.")
        except Exception:
            pass
    return default_prices


def post_product(api_url: str, product: Dict[str, Any]):
    headers = {"Content-Type": "application/json"}
    r = requests.post(api_url, headers=headers, data=json.dumps(product), timeout=5)
    r.raise_for_status()
    return r.json()


def main(argv):
    if len(argv) < 2:
        print("Usage: python3 billing_vision_only.py modelfile.eim [camera_id]")
        sys.exit(2)

    model_path = argv[1]
    if not os.path.exists(model_path):
        # try relative to script dir
        script_dir = os.path.dirname(os.path.realpath(__file__))
        candidate = os.path.join(script_dir, model_path)
        if os.path.exists(candidate):
            model_path = candidate

    api_url = os.environ.get("SMART_GROCERY_BOX_API_URL", "http://localhost:3000/product")
    threshold = float(os.environ.get("SMART_GROCERY_BOX_THRESHOLD", "0.90"))
    streak_frames = int(os.environ.get("SMART_GROCERY_BOX_STREAK_FRAMES", "8"))
    cooldown_s = float(os.environ.get("SMART_GROCERY_BOX_COOLDOWN_SECONDS", "2.0"))
    unit = os.environ.get("SMART_GROCERY_BOX_UNIT", "pcs")

    # Select camera
    if len(argv) >= 3:
        cam_id = int(argv[2])
    else:
        ports = get_webcams()
        if not ports:
            raise RuntimeError("No webcams found. Check your USB camera and try again.")
        if len(ports) > 1:
            print(f"[Smart-Grocery-Box] Multiple cameras found: {ports}. Using {ports[0]}.")
        cam_id = int(ports[0])

    print(f"[Smart-Grocery-Box] Model: {model_path}")
    print(f"[Smart-Grocery-Box] Camera ID: {cam_id}")
    print(f"[AutoBill] API URL: {api_url}")
    print(f"[AutoBill] threshold={threshold}, streak_frames={streak_frames}, cooldown_s={cooldown_s}")

    cart: Dict[int, Dict[str, Any]] = {}
    last_sent = 0.0
    current_label = None
    streak = 0

    runner = None
    with ImageImpulseRunner(model_path) as runner:
        model_info = runner.init()
        labels = model_info["model_parameters"]["labels"]

        # stable numeric ids per label
        label_to_id = {label: i + 1 for i, label in enumerate(labels)}
        prices = load_prices(labels)

        print("[AutoBill] Labels:", labels)

        next_frame = 0  # ~10 fps cap
        for res, img in runner.classifier(cam_id):
            if next_frame > now_ms():
                time.sleep((next_frame - now_ms()) / 1000.0)

            if "classification" not in res["result"]:
                next_frame = now_ms() + 100
                continue

            scores = res["result"]["classification"]
            best_label = max(labels, key=lambda l: scores.get(l, 0.0))
            best_score = float(scores.get(best_label, 0.0))

            # basic console logging
            print(f"[AutoBill] {best_label}: {best_score:.3f}", flush=True)

            if best_score >= threshold:
                if best_label == current_label:
                    streak += 1
                else:
                    current_label = best_label
                    streak = 1
            else:
                current_label = None
                streak = 0

            can_send = (time.time() - last_sent) >= cooldown_s
            if current_label and streak >= streak_frames and can_send:
                pid = label_to_id[current_label]
                price = float(prices.get(current_label, 0.0))

                if pid not in cart:
                    cart[pid] = {
                        "id": pid,
                        "name": current_label,
                        "price": price,
                        "unit": unit,
                        "taken": 0,
                        "payable": 0.0
                    }

                cart[pid]["taken"] += 1
                cart[pid]["payable"] = float(cart[pid]["taken"]) * price

                try:
                    resp = post_product(api_url, cart[pid])
                    print(f"[AutoBill] Added -> {resp}")
                except Exception as e:
                    print(f"[AutoBill] ERROR posting to API: {e}")

                last_sent = time.time()
                # reset streak so we don't instantly add again
                streak = 0
                current_label = None

            next_frame = now_ms() + 100


if __name__ == "__main__":
    main(sys.argv)
