import fs from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

function getProjectRoot() {
  if (process.env.PROJECT_ROOT) {
    return path.resolve(process.env.PROJECT_ROOT);
  }

  const cwd = process.cwd();
  return path.basename(cwd).toLowerCase() === "dashboard" ? path.dirname(cwd) : cwd;
}

function resolveAllowedVideoPath(rawPath) {
  const projectRoot = getProjectRoot();
  const outputRoot = path.resolve(projectRoot, "output");
  const normalizedInput = rawPath.replaceAll("/", path.sep).replaceAll("\\", path.sep);
  const absolute = path.isAbsolute(normalizedInput)
    ? path.resolve(normalizedInput)
    : path.resolve(projectRoot, normalizedInput);

  if (!absolute.startsWith(outputRoot)) {
    throw new Error("Only files inside /output are allowed.");
  }
  return absolute;
}

export async function GET(request) {
  const input = request.nextUrl.searchParams.get("path");
  if (!input) {
    return NextResponse.json({ error: "Missing path query param." }, { status: 400 });
  }

  try {
    const absolute = resolveAllowedVideoPath(input);
    const stat = await fs.stat(absolute);
    const range = request.headers.get("range");

    if (!range) {
      const file = await fs.readFile(absolute);
      return new NextResponse(file, {
        headers: {
          "Accept-Ranges": "bytes",
          "Cache-Control": "no-store",
          "Content-Length": String(stat.size),
          "Content-Type": "video/mp4"
        }
      });
    }

    const match = /^bytes=(\d+)-(\d*)$/.exec(range);
    if (!match) {
      return new NextResponse("Invalid range request", { status: 416 });
    }

    const start = Number(match[1]);
    const end = match[2] ? Number(match[2]) : stat.size - 1;

    if (Number.isNaN(start) || Number.isNaN(end) || start > end || end >= stat.size) {
      return new NextResponse("Requested range not satisfiable", {
        status: 416,
        headers: { "Content-Range": `bytes */${stat.size}` }
      });
    }

    const chunk = await fs.readFile(absolute);
    const body = chunk.subarray(start, end + 1);

    return new NextResponse(body, {
      status: 206,
      headers: {
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
        "Content-Length": String(end - start + 1),
        "Content-Range": `bytes ${start}-${end}/${stat.size}`,
        "Content-Type": "video/mp4"
      }
    });
  } catch (error) {
    return NextResponse.json({ error: error.message || "Cannot read video file." }, { status: 404 });
  }
}
