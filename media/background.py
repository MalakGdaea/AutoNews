import argparse
import os
import subprocess

BACKGROUND_PATH = "media/backgrounds/channel_bg.mp4"
DEFAULT_DURATION = 120


def generate_channel_background(duration: int = DEFAULT_DURATION, force: bool = False) -> str | None:
    """Render a loopable news-style background with kinetic gradients and branding cues."""
    print("Generating channel background...")
    os.makedirs("media/backgrounds", exist_ok=True)

    if os.path.exists(BACKGROUND_PATH):
        if force:
            os.remove(BACKGROUND_PATH)
            print("Removed existing background for regeneration.")
        else:
            print(f"Background already exists → {BACKGROUND_PATH}")
            return BACKGROUND_PATH

    filter_complex = f"""
        [0:v]
            geq=
                r='clip(15+110*sin(T*0.25+X*0.02)+45*sin(T*0.4+Y*0.02),0,255)'
                :g='clip(10+100*sin(T*0.24+X*0.018)+40*cos(T*0.35+Y*0.015),0,255)'
                :b='clip(30+130*cos(T*0.2+X*0.018)+55*sin(T*0.33+Y*0.013),0,255)'
        ,
            noise=alls=20:allf=t+0.6:seed=2,
            boxblur=2:1,
            drawgrid=w=120:h=40:color=0x99d6ff@0.08:t=1,
            colorchannelmixer=rr=0.92:gg=0.98:bb=1,
            drawbox=x=0:y=0:w=1080:h=160:color=0x03112a@0.85:t=fill,
            drawbox=x=0:y=1600:w=1080:h=320:color=0x020412@0.8:t=fill,
            drawbox=x=0:y=720:w=1080:h=120:color=0x021b3f@0.6:t=fill,
            drawtext=text='WORLD NEWS 24 SURVEILLANCE':fontcolor=0xC2E5FF:fontsize=48:x=60:y=40:font=Sans:alpha=0.95,
            drawtext=text='LIVE GLOBAL REPORTS':fontcolor=0xA8C9FF:fontsize=32:x=60:y=110:font=Sans:alpha=0.8,
            drawtext=text='STREAMING 24/7':fontcolor=0x7EF4FF:fontsize=24:x=60:y=1640:font=Sans:alpha=0.7
        [outv]
        """

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x050812:size=1080x1920:duration={duration}:rate=30",
        "-filter_complex",
        filter_complex,
        "-map",
        "[outv]",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-r",
        "30",
        "-t",
        str(duration),
        BACKGROUND_PATH,
    ]

    try:
        print("Rendering background (30+ seconds)...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            size_mb = os.path.getsize(BACKGROUND_PATH) / (1024 * 1024)
            print(f"Background generated → {BACKGROUND_PATH} ({size_mb:.1f} MB)")
            return BACKGROUND_PATH
        print(f"FFmpeg error:\n{result.stderr[-500:]}")
        return None
    except Exception as error:
        print(f"Error while generating background: {error}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a branded channel background.")
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=DEFAULT_DURATION,
        help="Duration of the background loop in seconds.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the existing background even if it already exists.",
    )
    args = parser.parse_args()
    generate_channel_background(duration=args.duration, force=args.force)
