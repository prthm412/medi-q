import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getAnalyticsSummary } from "@/api/analytics";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { AnalyticsSummary } from "@/types";

export function AnalyticsPanel() {
  const [days, setDays] = useState("14");
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    getAnalyticsSummary(Number(days)).then(setSummary);
  }, [days]);

  if (!summary) return <p className="text-sm text-slate-500">Loading...</p>;

  const totalBooked = summary.days.reduce((sum, d) => sum + d.booked, 0);
  const avgOccupancy =
    summary.days.reduce((sum, d) => sum + d.occupancy_pct, 0) / summary.days.length;

  const chartData = summary.days.map((d) => ({
    label: d.date.slice(5),
    occupancy: d.occupancy_pct,
  }));

  return (
    <div className="space-y-4">
      <div className="w-40">
        <Select value={days} onValueChange={setDays}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="14">Last 14 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Appointments</p>
            <p className="text-2xl font-bold">{totalBooked}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">Avg. occupancy</p>
            <p className="text-2xl font-bold">{avgOccupancy.toFixed(1)}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-slate-500">No-show rate</p>
            <p className="text-2xl font-bold">{summary.no_show_rate_pct}%</p>
          </CardContent>
        </Card>
      </div>

      <div style={{ height: 260 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" />
            <YAxis unit="%" />
            <Tooltip formatter={(value) => `${value}%`} />
            <Bar dataKey="occupancy" name="Occupancy" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}