import { useEffect, useRef, useState } from "react";
import { getMyPatientProfile, getPatientAppointments } from "@/api/patients";
import { checkIn } from "@/api/queue";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Appointment, QueuePositionUpdate } from "@/types";

export function QueueWidget() {
  const [todaysAppointment, setTodaysAppointment] = useState<Appointment | null>(null);
  const [patientId, setPatientId] = useState<string>("");
  const [checkedIn, setCheckedIn] = useState(false);
  const [position, setPosition] = useState<number | null>(null);
  const [waitMinutes, setWaitMinutes] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    async function load() {
      const patient = await getMyPatientProfile();
      setPatientId(patient.id);
      const appointments = await getPatientAppointments(patient.id);
      const today = new Date().toDateString();
      const match = appointments.find(
        (a) => a.status === "scheduled" && new Date(a.scheduled_time).toDateString() === today
      );
      setTodaysAppointment(match ?? null);
    }
    load();
  }, []);

  function connectWebSocket(doctorId: string) {
    const token = localStorage.getItem("mediqueue_token");
    const wsUrl = `ws://localhost:8000/ws/queue/${doctorId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      const data: QueuePositionUpdate = JSON.parse(event.data);
      if (data.type === "position_update" && data.patient_id === patientId) {
        setPosition(data.position);
        setWaitMinutes(data.estimated_wait_minutes);
      }
    };
    wsRef.current = ws;
  }

  useEffect(() => {
    return () => wsRef.current?.close();
  }, []);

  async function handleCheckIn() {
    if (!todaysAppointment) return;
    const result = await checkIn(todaysAppointment.id);
    setPosition(result.position);
    setWaitMinutes(result.estimated_wait_minutes);
    setCheckedIn(true);
    connectWebSocket(todaysAppointment.doctor_id);
  }

  if (!todaysAppointment) {
    return <p className="text-sm text-slate-500">No appointment scheduled for today.</p>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Live Queue</CardTitle>
      </CardHeader>
      <CardContent>
        {!checkedIn ? (
          <Button onClick={handleCheckIn}>Check in</Button>
        ) : (
          <div className="space-y-1">
            <p>Position: <span className="font-bold">{position}</span></p>
            <p>Estimated wait: <span className="font-bold">{waitMinutes} min</span></p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}