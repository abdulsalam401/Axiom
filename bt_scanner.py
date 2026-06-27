#!/usr/bin/env python3
"""
Bluetooth Scanner using Bleak (Works on Windows)
"""

import asyncio
from datetime import datetime
from bleak import BleakScanner, BleakClient

async def scan_devices(timeout=5):
    """Scan for Bluetooth devices"""
    print(f"[*] Scanning for Bluetooth devices (timeout: {timeout}s)...")
    
    devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    
    results = []
    for device, adv_data in devices.values():
        results.append({
            'address': device.address,
            'name': device.name or 'Unknown',
            'rssi': adv_data.rssi if adv_data else 'N/A',
            'uuids': adv_data.service_uuids if adv_data else []
        })
        print(f"[+] Found: {device.name or 'Unknown'} ({device.address})")
    
    return results

async def connect_and_read_info(address):
    """Connect to a device and read info"""
    try:
        async with BleakClient(address) as client:
            print(f"[+] Connected to {address}")
            print(f"[+] Services:")
            for service in client.services:
                print(f"    - {service.uuid}: {service.description}")
            return True
    except Exception as e:
        print(f"[-] Failed to connect: {e}")
        return False

def main():
    import asyncio
    
    print("\n" + "="*60)
    print("  Bluetooth Scanner (Bleak)")
    print("="*60 + "\n")
    
    # Scan for devices
    devices = asyncio.run(scan_devices(5))
    
    if not devices:
        print("\n[!] No Bluetooth devices found.")
        print("[!] Make sure Bluetooth is enabled on your computer.")
        return
    
    print(f"\n[+] Found {len(devices)} devices")
    print("\n" + "-"*60)
    print(f"{'Name':<30} {'Address':<20} {'RSSI':<10}")
    print("-"*60)
    
    for d in devices:
        name = d['name'][:30] if d['name'] else 'Unknown'
        print(f"{name:<30} {d['address']:<20} {d['rssi']:<10}")
    
    print("-"*60 + "\n")

if __name__ == "__main__":
    main()