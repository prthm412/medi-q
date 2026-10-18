import { useEffect, useState } from "react";
import { getMyDoctorAppointments } from "@/api/doctors";
import { getPatient } from "@/api/patients";
import { updateAppointmentStatus } from "@/api/appointments";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { MedicalRecordsPanel } from "./MedicalRecordsPanel";
import type { Appointment, Patient, AppointmentStatus } from "@/types";
import { downloadPrescription } from "@/api/documents";

const statusVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  scheduled: "default",
  in_progress: "secondary",
  completed: "outline",
  no_show: "destructive",
};

export function TodaysSchedule() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [patients, setPatients] = useState<Record<string, Patient>>({});
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

  async function load() {
    const all = await getMyDoctorAppointments();
    const today = new Date().toDateString();
    const todays = all.filter((a) => new Date(a.scheduled_time).toDateString() === today);
    setAppointments(todays);

    const patientMap: Record<string, Patient> = {};
    await Promise.all(
      todays.map(async (a) => {
        if (!patientMap[a.patient_id]) {
          patientMap[a.patient_id] = await getPatient(a.patient_id);
        }
      })
    );
    setPatients(patientMap);
  }

    async function handlePrescription(appointmentId: string) {
    try {
      await downloadPrescription(appointmentId);
    } catch {
      alert("No prescription available for this visit.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleMarkComplete(appointmentId: string) {
    await updateAppointmentStatus(appointmentId, "completed" as AppointmentStatus);
    load();
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Patient</TableHead>
            <TableHead>Urgency</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {appointments.map((a) => (
            <TableRow key={a.id}>
              <TableCell>{new Date(a.scheduled_time).toLocaleTimeString()}</TableCell>
              <TableCell>{patients[a.patient_id]?.name ?? "..."}</TableCell>
              <TableCell>{a.urgency_level}</TableCell>
              <TableCell><Badge variant={statusVariant[a.status]}>{a.status}</Badge></TableCell>
              <TableCell className="space-x-2">
                <Button size="sm" variant="outline" onClick={() => setSelectedAppointment(a)}>
                  Notes
                </Button>
                {a.status !== "completed" && (
                  <Button size="sm" onClick={() => handleMarkComplete(a.id)}>
                    Mark Complete
                  </Button>
                )}
                {a.status === "completed" && (
                  <Button size="sm" variant="outline" onClick={() => handlePrescription(a.id)}>
                    Prescription
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={!!selectedAppointment} onOpenChange={(open) => !open && setSelectedAppointment(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Visit Notes</DialogTitle>
          </DialogHeader>
          {selectedAppointment && (
            <MedicalRecordsPanel
              patientId={selectedAppointment.patient_id}
              appointmentId={selectedAppointment.id}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}