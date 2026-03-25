import { spawn } from "node:child_process";
import path from "node:path";
import { NextResponse } from "next/server";

function getProjectRoot() {
    if (process.env.PROJECT_ROOT) {
        return path.resolve(process.env.PROJECT_ROOT);
    }
    const cwd = process.cwd();
    return path.basename(cwd).toLowerCase() === "dashboard" ? path.dirname(cwd) : cwd;
}

function runManualUpload(projectRoot, id) {
    const pythonBin = process.env.PYTHON_BIN || "python3";
    return new Promise((resolve, reject) => {
        const child = spawn(pythonBin, ["-m", "tiktok.manual_upload", String(id)], {
            cwd: projectRoot,
            env: process.env,
            stdio: ["ignore", "pipe", "pipe"],
        });

        let stdout = "";
        let stderr = "";

        child.stdout.on("data", (chunk) => {
            stdout += chunk.toString();
        });
        child.stderr.on("data", (chunk) => {
            stderr += chunk.toString();
        });

        child.on("error", (error) => reject(error));
        child.on("close", (code) => {
            if (code !== 0) {
                const details = stderr.trim() || stdout.trim() || `Process exited with code ${code}`;
                reject(new Error(details));
                return;
            }
            resolve(stdout);
        });
    });
}

function extractJsonMarker(output) {
    const line = output
        .split(/\r?\n/)
        .reverse()
        .find((entry) => entry.startsWith("__JSON__"));

    if (!line) return null;

    try {
        return JSON.parse(line.slice("__JSON__".length));
    } catch {
        return null;
    }
}

export async function PATCH(_request, { params }) {
    const id = Number(params.id);
    if (!Number.isFinite(id)) {
        return NextResponse.json({ error: "Invalid video id." }, { status: 400 });
    }

    try {
        const projectRoot = getProjectRoot();
        const raw = await runManualUpload(projectRoot, id);
        const payload = extractJsonMarker(raw);
        return NextResponse.json({ ok: true, result: payload || null });
    } catch (error) {
        return NextResponse.json({ error: error.message || "Upload failed." }, { status: 500 });
    }
}
