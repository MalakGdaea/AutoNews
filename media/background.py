import ffmpeg
import os
import subprocess

BACKGROUND_PATH = "media/backgrounds/channel_bg.mp4"

def generate_channel_background(duration: int = 120):
    """
    Generate a loopable branded news channel background.
    Dark space + rotating globe wireframe + subtle glow.
    Generated once and reused for all videos.
    """
    print("🌍 Generating channel background...")
    os.makedirs("media/backgrounds", exist_ok=True)

    if os.path.exists(BACKGROUND_PATH):
        print(f"✅ Background already exists → {BACKGROUND_PATH}")
        return BACKGROUND_PATH

    # FFmpeg complex filter to create globe animation
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0a0a1a:size=1080x1920:duration={duration}:rate=30",
        "-f", "lavfi",
        "-i", f"color=c=0x0a0a1a:size=1080x1920:duration={duration}:rate=30",
        "-filter_complex",
        f"""
        [0:v]
        geq=
            r='if(
                lt(
                    hypot(X-540, Y-860),
                    300
                ),
                if(
                    lt(
                        mod(
                            sqrt(pow(X-540,2)+pow(Y-860,2)) * 0.05 + T*8,
                            6.28
                        ),
                        0.3
                    ),
                    180,
                    if(
                        lt(
                            mod(
                                atan2(Y-860, X-540) * 4 + T*6,
                                6.28
                            ),
                            0.2
                        ),
                        150,
                        20
                    )
                ),
                if(lt(Y, 1750), 10, if(lt(Y,1760), 180, 10))
            )':
            g='if(
                lt(
                    hypot(X-540, Y-860),
                    300
                ),
                if(
                    lt(
                        mod(
                            sqrt(pow(X-540,2)+pow(Y-860,2)) * 0.05 + T*8,
                            6.28
                        ),
                        0.3
                    ),
                    60,
                    if(
                        lt(
                            mod(
                                atan2(Y-860, X-540) * 4 + T*6,
                                6.28
                            ),
                            0.2
                        ),
                        50,
                        15
                    )
                ),
                if(lt(Y, 1750), 10, if(lt(Y,1760), 20, 10))
            )':
            b='if(
                lt(
                    hypot(X-540, Y-860),
                    300
                ),
                if(
                    lt(
                        mod(
                            sqrt(pow(X-540,2)+pow(Y-860,2)) * 0.05 + T*8,
                            6.28
                        ),
                        0.3
                    ),
                    255,
                    if(
                        lt(
                            mod(
                                atan2(Y-860, X-540) * 4 + T*6,
                                6.28
                            ),
                            0.2
                        ),
                        200,
                        30
                    )
                ),
                if(lt(Y, 1750), 26, if(lt(Y,1760), 30, 26))
            )',

        gblur=sigma=2,

        drawbox=
            x=0:y=1750:w=1080:h=80:
            color=0xCC0000@0.9:t=fill,

        drawtext=
            text='BREAKING NEWS':
            fontcolor=white:
            fontsize=42:
            x=(w-text_w)/2:
            y=1770:
            font=Sans:
            fontcolor_expr=white,

        drawtext=
            text='● LIVE':
            fontcolor=0xFFFFFF:
            fontsize=30:
            x=40:
            y=1778:
            font=Sans,

        drawtext=
            text='WORLD NEWS 24':
            fontcolor=0xCCCCCC:
            fontsize=36:
            x=(w-text_w)/2:
            y=80:
            font=Sans:
            alpha=0.8
        [outv]
        """,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-r", "30",
        "-t", str(duration),
        BACKGROUND_PATH
    ]

    try:
        print("⏳ Rendering background (this takes ~30 seconds)...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            size_mb = os.path.getsize(BACKGROUND_PATH) / (1024 * 1024)
            print(f"✅ Background generated → {BACKGROUND_PATH} ({size_mb:.1f} MB)")
            return BACKGROUND_PATH
        else:
            print(f"❌ FFmpeg error:\n{result.stderr[-500:]}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    generate_channel_background()