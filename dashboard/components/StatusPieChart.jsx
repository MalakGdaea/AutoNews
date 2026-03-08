"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#1CC88A", "#FFB020", "#60A5FA", "#EF4444", "#9CA3AF", "#FB7185"];

export default function StatusPieChart({ data }) {
  return (
    <section className="glass animate-rise rounded-2xl p-4 shadow-panel md:p-5">
      <h2 className="text-lg font-semibold">Status Distribution</h2>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} innerRadius={52} outerRadius={92} dataKey="value" nameKey="name" paddingAngle={2}>
              {data.map((entry, index) => (
                <Cell key={`${entry.name}-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "#161B22", border: "1px solid #2d333b", borderRadius: "12px" }}
              formatter={(value, name) => [value, String(name)]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
        {data.map((entry, index) => (
          <p key={entry.name} className="truncate text-muted">
            <span className="mr-2 inline-block h-2 w-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
            {entry.name} ({entry.value})
          </p>
        ))}
      </div>
    </section>
  );
}
