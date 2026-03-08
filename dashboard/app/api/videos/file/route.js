import fs from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

function resolveAllowedVideoPath(rawPath) {
  const projectRoot = process.env.PROJECT_ROOT || process.cwd().replace(/\\dashboard$/, "");
  const outputRoot = path.resolve(projectRoot, "output");

  const incoming = rawPath.replaceAll("\\", "/");
  const absolute = path.isAbsolute(incoming) ? path.resolve(incoming) : path.resolve(projectRoot, incoming);

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
    const file = await fs.readFile(absolute);
    return new NextResponse(file, {
      headers: {
        "Content-Type": "video/mp4",
        "Cache-Control": "no-store"
      }
    });
  } catch (error) {
    return NextResponse.json({ error: error.message || "Cannot read video file." }, { status: 404 });
  }
}
