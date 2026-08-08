import { useEffect, useState } from "react";
import { getMyPatientProfile, getPatientAppointments } from "@/api/patients";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { Appointment } from "@/types";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  scheduled: "default",
  in_progress: "secondary",
  completed: "outline",
  no_show: "destructive",
};

export function AppointmentHistory() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const patient = await getMyPatientProfile();
      const data = await getPatientAppointments(patient.id);
      setAppointments(data);
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <p className="text-sm text-slate-500">Loading...</p>;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Urgency</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {appointments.map((a) => (
          <TableRow key={a.id}>
            <TableCell>{new Date(a.scheduled_time).toLocaleString()}</TableCell>
            <TableCell>
              <Badge variant={statusVariant[a.status]}>{a.status}</Badge>
            </TableCell>
            <TableCell>{a.urgency_level}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}