"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function PostingFrequencyChart({ data }) {
  return (
    <section className="glass animate-rise rounded-2xl p-4 shadow-panel md:p-5">
      <h2 className="text-lg font-semibold">Posting Frequency (7d)</h2>
      <div className="mt-4 h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#243042" />
            <XAxis dataKey="day" stroke="#8B949E" />
            <YAxis stroke="#8B949E" allowDecimals={false} />
            <Tooltip
              contentStyle={{ background: "#161B22", border: "1px solid #2d333b", borderRadius: "12px" }}
              cursor={{ fill: "rgba(28, 200, 138, 0.12)" }}
            />
            <Bar dataKey="posts" fill="#1CC88A" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
