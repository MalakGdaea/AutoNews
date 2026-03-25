import { NextResponse } from "next/server";
import fs from "node:fs/promises";
import path from "node:path";
import { getSupabaseServerClient } from "@/lib/supabaseAdmin";

function getProjectRoot() {
    if (process.env.PROJECT_ROOT) {
        return path.resolve(process.env.PROJECT_ROOT);
    }
    const cwd = process.cwd();
    return path.basename(cwd).toLowerCase() === "dashboard" ? path.dirname(cwd) : cwd;
}

function parseSupabaseStoragePath(rawUrl) {
    if (!rawUrl || typeof rawUrl !== "string") return null;

    // Handle plain object paths such as "videos/foo.mp4" when bucket is configured.
    const configuredBucket = process.env.SUPABASE_STORAGE_BUCKET;
    if (!rawUrl.includes("://") && configuredBucket) {
        const normalized = rawUrl.replace(/^\/+/, "");
        if (normalized.startsWith(`${configuredBucket}/`)) {
            return {
                bucket: configuredBucket,
                objectPath: normalized.slice(configuredBucket.length + 1),
            };
        }
        return { bucket: configuredBucket, objectPath: normalized };
    }

    try {
        const url = new URL(rawUrl);
        const patterns = [
            /\/storage\/v1\/object\/public\/([^/]+)\/(.+)$/,
            /\/storage\/v1\/object\/sign\/([^/]+)\/(.+)$/,
            /\/storage\/v1\/object\/authenticated\/([^/]+)\/(.+)$/,
        ];

        const matched = patterns
            .map((pattern) => url.pathname.match(pattern))
            .find(Boolean);

        if (!matched) return null;

        const bucket = matched[1];
        const objectPath = decodeURIComponent(matched[2]);
        const parts = objectPath.split("/");
        if (!bucket || parts.length === 0) return null;
        return { bucket, objectPath: parts.join("/") };
    } catch {
        return null;
    }
}

function isNotFoundStorageError(message = "") {
    const lowered = message.toLowerCase();
    return lowered.includes("not found") || lowered.includes("no such file");
}

async function deleteLocalIfAllowed(rawPath) {
    if (!rawPath || rawPath.startsWith("http://") || rawPath.startsWith("https://")) {
        return;
    }

    const projectRoot = getProjectRoot();
    const outputRoot = path.resolve(projectRoot, "output");
    const normalizedInput = rawPath.replaceAll("/", path.sep).replaceAll("\\", path.sep);
    const absolute = path.isAbsolute(normalizedInput)
        ? path.resolve(normalizedInput)
        : path.resolve(projectRoot, normalizedInput);

    if (!absolute.startsWith(outputRoot)) return;

    try {
        await fs.unlink(absolute);
    } catch {
        // Best effort: ignore missing or inaccessible files.
    }
}

export async function DELETE(_request, { params }) {
    const id = Number(params.id);
    if (!Number.isFinite(id)) {
        return NextResponse.json({ error: "Invalid video id." }, { status: 400 });
    }

    try {
        const supabase = getSupabaseServerClient();
        const { data: row, error: readError } = await supabase
            .from("videos")
            .select("id,video_path,video_url")
            .eq("id", id)
            .single();

        if (readError) {
            return NextResponse.json({ error: readError.message }, { status: 500 });
        }

        const candidates = [row?.video_url, row?.video_path]
            .map((value) => parseSupabaseStoragePath(value || ""))
            .filter(Boolean);

        // Dedupe bucket/path pairs.
        const uniqueTargets = Array.from(new Map(candidates.map((t) => [`${t.bucket}:${t.objectPath}`, t])).values());

        for (const target of uniqueTargets) {
            const { error: storageError } = await supabase.storage
                .from(target.bucket)
                .remove([target.objectPath]);

            if (storageError && !isNotFoundStorageError(storageError.message)) {
                return NextResponse.json(
                    {
                        error: `Storage delete failed for ${target.bucket}/${target.objectPath}: ${storageError.message}`,
                    },
                    { status: 500 }
                );
            }
        }

        await deleteLocalIfAllowed(row?.video_path || "");

        const { error } = await supabase.from("videos").delete().eq("id", id);

        if (error) {
            return NextResponse.json({ error: error.message }, { status: 500 });
        }

        return NextResponse.json({ ok: true });
    } catch (error) {
        return NextResponse.json({ error: error.message || "Unexpected error." }, { status: 500 });
    }
}
