#!/usr/bin/env python3
"""
Photo Sorter - simple CLI image organizer and EXIF reporter
Usage: python3 photo_sorter.py <input_folder> [--by date|camera] [--report report.csv]
Example: python3 photo_sorter.py ./example_photos --by date --report report.csv
"""
import sys, os, csv, shutil, argparse
from PIL import Image, ExifTags
from datetime import datetime

def get_exif(path):
    try:
        img = Image.open(path)
        exif_raw = img._getexif()
        if not exif_raw:
            return {}
        exif = {}
        for tag, val in exif_raw.items():
            decoded = ExifTags.TAGS.get(tag, tag)
            exif[decoded] = val
        return exif
    except Exception:
        return {}

def get_date_from_exif(exif):
    dt = exif.get('DateTimeOriginal') or exif.get('DateTime') or ''
    if isinstance(dt, bytes):
        dt = dt.decode(errors='ignore')
    if dt:
        try:
            # common format: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(dt, "%Y:%m:%d %H:%M:%S").date().isoformat()
        except Exception:
            pass
    return ''

def get_camera_from_exif(exif):
    return exif.get('Model', '') or exif.get('Make', '')

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def is_image_file(fname):
    ext = fname.lower().rsplit('.',1)
    if len(ext) == 1: return False
    return ext[1] in ('jpg','jpeg','png','tiff','heic')

def process_folder(infolder, by='date', report='report.csv', move_files=False):
    infolder = os.path.abspath(infolder)
    out_base = os.path.join(infolder, 'sorted_by_' + by)
    ensure_dir(out_base)

    rows = []
    for entry in sorted(os.listdir(infolder)):
        full = os.path.join(infolder, entry)
        if not os.path.isfile(full) or not is_image_file(entry):
            continue
        exif = get_exif(full)
        date = get_date_from_exif(exif)
        cam = get_camera_from_exif(exif)
        if by == 'date' and date:
            target_dir = os.path.join(out_base, date)
        elif by == 'camera' and cam:
            safe_cam = "".join(c for c in cam if c.isalnum() or c in " _-").strip() or "UnknownCamera"
            target_dir = os.path.join(out_base, safe_cam)
        else:
            target_dir = os.path.join(out_base, 'unsorted')

        ensure_dir(target_dir)
        dest = os.path.join(target_dir, entry)
        # copy - keeps original intact
        shutil.copy2(full, dest)

        rows.append({
            'filename': entry,
            'date': date,
            'camera': cam,
            'orig_path': full,
            'dest_path': dest
        })
        print(f"[+] {entry} -> {os.path.relpath(dest, infolder)}")

    # write report
    report_path = os.path.join(infolder, report)
    with open(report_path, 'w', newline='', encoding='utf-8') as csvf:
        writer = csv.DictWriter(csvf, fieldnames=['filename','date','camera','orig_path','dest_path'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\nReport written to: {report_path}")
    print(f"Sorted output folder: {out_base}")
    return report_path, out_base

def main():
    p = argparse.ArgumentParser(description="Photo Sorter - organize images by EXIF date or camera")
    p.add_argument('input_folder')
    p.add_argument('--by', choices=['date','camera'], default='date')
    p.add_argument('--report', default='report.csv')
    args = p.parse_args()
    if not os.path.isdir(args.input_folder):
        print("Input folder doesn't exist:", args.input_folder)
        sys.exit(1)
    process_folder(args.input_folder, by=args.by, report=args.report)

if __name__ == "__main__":
    main()
