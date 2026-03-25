import { NextResponse } from "next/server";

// Maximum time Vercel will wait for the Oracle worker (ms).
// Increase if uploads regularly time out. Requires a Vercel Pro plan
// for values above 10 000.
export const maxDuration = 300;

async function callOracleUpload(id) {
    const baseUrl = (process.env.ORACLE_API_URL || "").replace(/\/$/, "");
    const secret = process.env.ORACLE_API_SECRET || "";

    if (!baseUrl) {
        throw new Error(
            "ORACLE_API_URL is not set. Add it to your Vercel environment variables " +
            "(e.g. http://<oracle-ip>:8080)."
        );
    }
    if (!secret) {
        throw new Error(
            "ORACLE_API_SECRET is not set. Add it to your Vercel environment variables."
        );
    }

    const url = `${baseUrl}/api/upload/${id}`;
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Secret": secret,
        },
    });

    let body;
    try {
        body = await response.json();
    } catch {
        const text = await response.text().catch(() => "");
        throw new Error(`Oracle worker returned non-JSON (HTTP ${response.status}): ${text}`);
    }

    if (!response.ok || body.ok === false) {
        throw new Error(body.error || `Oracle worker HTTP ${response.status}`);
    }

    return body.result ?? null;
}

export async function PATCH(_request, { params }) {
    const id = Number(params.id);
    if (!Number.isFinite(id)) {
        return NextResponse.json({ error: "Invalid video id." }, { status: 400 });
    }

    try {
        const result = await callOracleUpload(id);
        return NextResponse.json({ ok: true, result });
    } catch (error) {
        return NextResponse.json({ error: error.message || "Upload failed." }, { status: 500 });
    }
}
