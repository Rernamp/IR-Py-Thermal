#!/usr/bin/env python3

import argparse
import time
import numpy as np
import cv2
from datetime import datetime
from pathlib import Path

import irpythermal


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Capture single photo from thermal camera")
    parser.add_argument(
        "-r", "--rawcam", action="store_true", help="use the raw camera"
    )
    parser.add_argument(
        "-d", "--device", type=str, help="use the camera at camera_path"
    )
    parser.add_argument(
        "-o", "--offset", type=float, help="set a fixed offset for the temperature data"
    )
    parser.add_argument(
        "-s", "--stabilization", type=int, default=10,
        help="number of frames to skip for stabilization (default: 10)"
    )
    parser.add_argument(
        "-f", "--output-folder", type=str, default=".",
        help="output folder for images (default: current directory)"
    )
    parser.add_argument(
        "--high-range", action="store_true",
        help="use high temperature range (supported by T2S+/T2L)"
    )
    parser.add_argument(
        "file", nargs="?", type=str, help="use the emulator with the data in file.npy"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    
    # Create output folder if it doesn't exist
    output_folder = Path(args.output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Initialize camera
    print("Initializing camera...")
    if args.file and args.file.endswith(".npy"):
        camera = irpythermal.CameraEmulator(args.file)
        print(f"Using emulator with file: {args.file}")
    else:
        camera_kwargs = {}
        if args.rawcam:
            camera_kwargs["camera_raw"] = True
        if args.device:
            camera_path = args.device
            cv2_cam = cv2.VideoCapture(camera_path)
            camera_kwargs["video_dev"] = cv2_cam
        if args.offset:
            camera_kwargs["fixed_offset"] = args.offset
        
        camera = irpythermal.Camera(**camera_kwargs)
        
        # Set temperature range if requested
        if args.high_range:
            print("Setting high temperature range...")
            camera.temperature_range_high()
            camera.wait_for_range_application()
        else:
            print("Using normal temperature range...")
    
    print(f"Camera resolution: {camera.width} x {camera.height}")
    
    # Stabilization - skip initial frames
    print(f"Stabilizing (skipping {args.stabilization} frames)...")
    for i in range(args.stabilization):
        camera.read()
        if (i + 1) % 5 == 0:
            print(f"  Skipped {i + 1}/{args.stabilization} frames")
        time.sleep(0.01)  # Small delay between reads
    
    # Capture final frame
    print("Capturing final frame...")
    ret, raw_frame = camera.read()
    if not ret:
        print("Error: could not read frame from camera")
        camera.release()
        return
    
    # Get camera info for temperature conversion
    info, lut = camera.info()
    
    # Convert to temperature frame
    temp_frame = camera.convert_to_frame(raw_frame, lut)
    
    # Calculate min and max temperatures
    temp_min = np.min(temp_frame)
    temp_max = np.max(temp_frame)
    temp_mean = np.mean(temp_frame)
    temp_std = np.std(temp_frame)
    
    print(f"\nTemperature statistics:")
    print(f"  Min: {temp_min:.2f}°C")
    print(f"  Max: {temp_max:.2f}°C")
    print(f"  Mean: {temp_mean:.2f}°C")
    print(f"  Std: {temp_std:.2f}°C")
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Save temperature data as image
    # Normalize to 0-255 for image saving
    temp_normalized = ((temp_frame - temp_min) / (temp_max - temp_min) * 255).astype(np.uint8)
    
    # Apply colormap for visualization
    temp_colored = cv2.applyColorMap(temp_normalized, cv2.COLORMAP_INFERNO)
    
    # Save colored image
    image_filename = output_folder / f"thermal_{timestamp}.png"
    cv2.imwrite(str(image_filename), temp_colored)
    print(f"\nImage saved to: {image_filename}")
    
    # Save raw temperature data as numpy array
    numpy_filename = output_folder / f"thermal_{timestamp}.npy"
    np.save(str(numpy_filename), temp_frame)
    print(f"Raw temperature data saved to: {numpy_filename}")
    
    # Save metadata file with temperature statistics
    metadata_filename = output_folder / f"thermal_{timestamp}.txt"
    with open(metadata_filename, 'w') as f:
        f.write(f"Thermal Camera Capture\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Camera resolution: {camera.width} x {camera.height}\n")
        f.write(f"\nTemperature statistics:\n")
        f.write(f"  Minimum: {temp_min:.2f}°C\n")
        f.write(f"  Maximum: {temp_max:.2f}°C\n")
        f.write(f"  Mean: {temp_mean:.2f}°C\n")
        f.write(f"  Standard deviation: {temp_std:.2f}°C\n")
        
        # Add camera info if available
        if info:
            f.write(f"\nCamera info:\n")
            for key, value in info.items():
                f.write(f"  {key}: {value}\n")
    
    print(f"Metadata saved to: {metadata_filename}")
    
    # Optional: Save a simple text file with just min/max as requested
    simple_filename = output_folder / f"thermal_{timestamp}_minmax.txt"
    with open(simple_filename, 'w') as f:
        f.write(f"{temp_min:.2f}\n")
        f.write(f"{temp_max:.2f}\n")
    print(f"Min/max file saved to: {simple_filename}")
    
    # Release camera
    camera.release()
    print("\nDone!")


if __name__ == "__main__":
    main()