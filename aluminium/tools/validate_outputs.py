#!/usr/bin/env python3
"""Validate the exported aluminium videos (both languages, with and without music)."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    report = {"files": []}
    for lang in ["fr", "en"]:
        for version in ["musique", "sans-son"]:
            path = OUT / f"aluminium-60s-{lang}-{version}.mp4"
            probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_streams",
                                    "-show_format", "-of", "json", str(path)],
                                   text=True, capture_output=True, check=True)
            data = json.loads(probe.stdout)
            videos = [s for s in data["streams"] if s["codec_type"] == "video"]
            audios = [s for s in data["streams"] if s["codec_type"] == "audio"]
            assert len(videos) == 1, path.name
            v = videos[0]
            assert (v["width"], v["height"], v["r_frame_rate"], v["nb_read_frames"]) == (
                1920, 1080, "30/1", "1800"), v
            assert v["codec_name"] == "h264", v["codec_name"]
            assert abs(float(data["format"]["duration"]) - 60) < 0.05, data["format"]
            assert len(audios) == (1 if version == "musique" else 0), audios
            if audios:
                assert (audios[0]["codec_name"], audios[0]["sample_rate"], audios[0]["channels"]) == (
                    "aac", "48000", 2), audios[0]
            decode = subprocess.run(["ffmpeg", "-xerror", "-v", "error", "-i", str(path), "-f", "null", "-"],
                                    text=True, capture_output=True, check=True)
            assert not decode.stderr.strip(), decode.stderr
            report["files"].append({"file": path.name, "language": lang, "duration": 60, "frames": 1800,
                                    "dimensions": "1920x1080", "fps": 30, "full_decode": "passed",
                                    "audio": "AAC stereo 48kHz" if audios else None,
                                    "bytes": path.stat().st_size, "sha256": digest(path.read_bytes())})
            print("Validated export:", path.name, flush=True)
    (OUT / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")


if __name__ == "__main__":
    main()
