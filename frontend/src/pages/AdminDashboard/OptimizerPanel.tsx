import { useState } from "react";
import { format } from "date-fns";
import { optimizeSchedule } from "@/api/schedule";
import { listDoctors } from "@/api/doctors";
import { getPatient } from "@/api/patients";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ScheduleOptimizeResponse } from "@/types";

interface Row {
  patientName: string;
  doctorName: string;
  time: string;
  room: number;
}

export function OptimizerPanel() {
  const today = format(new Date(), "yyyy-MM-dd");
  const [date, setDate] = useState(today);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ScheduleOptimizeResponse | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");

  async function handleRun() {
    setRunning(true);
    setError("");
    try {
      const data = await optimizeSchedule(date);
      const doctors = await listDoctors();
      const doctorNames = Object.fromEntries(doctors.map((d) => [d.id, d.name]));

      const patientNames: Record<string, string> = {};
      await Promise.all(
        data.assignments.map(async (a) => {
          if (!patientNames[a.patient_id]) {
            patientNames[a.patient_id] = (await getPatient(a.patient_id)).name;
          }
        })
      );

      setRows(
        data.assignments.map((a) => ({
          patientName: patientNames[a.patient_id],
          doctorName: doctorNames[a.doctor_id] ?? a.doctor_id,
          time: new Date(a.scheduled_time).toLocaleString(),
          room: a.room_id,
        }))
      );
      setResult(data);
    } catch {
      setError("Optimization failed.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end gap-4">
        <div className="space-y-2">
          <Label htmlFor="opt-date">Date</Label>
          <Input
            id="opt-date"
            type="date"
            min={today}
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        <Button onClick={handleRun} disabled={running || !date}>
          {running ? "Running..." : "Run optimizer"}
        </Button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-2">
          <p className="text-sm text-slate-500">
            {result.assignments.length} appointment(s) scheduled, {result.unassigned_patient_ids.length} unassigned.
            Objective value: {result.objective_value}
          </p>
          {rows.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>Doctor</TableHead>
                  <TableHead>Time</TableHead>
                  <TableHead>Room</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((r, i) => (
                  <TableRow key={i}>
                    <TableCell>{r.patientName}</TableCell>
                    <TableCell>{r.doctorName}</TableCell>
                    <TableCell>{r.time}</TableCell>
                    <TableCell>{r.room}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      )}
    </div>
  );
}