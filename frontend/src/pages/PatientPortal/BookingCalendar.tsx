import { useState, useEffect } from "react";
import { Calendar, dateFnsLocalizer, type SlotInfo } from "react-big-calendar";
import format from "date-fns/format";
import parse from "date-fns/parse";
import startOfWeek from "date-fns/startOfWeek";
import getDay from "date-fns/getDay";
import enUS from "date-fns/locale/en-US";
import "react-big-calendar/lib/css/react-big-calendar.css";
import { listDoctors, getDoctorAvailability } from "@/api/doctors";
import { createAppointment } from "@/api/appointments";
import { getMyPatientProfile } from "@/api/patients";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import type { Doctor } from "@/types";

const locales = { "en-US": enUS };
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

interface SlotEvent {
  title: string;
  start: Date;
  end: Date;
}

export function BookingCalendar() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>("");
  const [events, setEvents] = useState<SlotEvent[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<Date | null>(null);
  const [urgencyLevel, setUrgencyLevel] = useState("3");
  const [booking, setBooking] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    listDoctors().then(setDoctors);
  }, []);

  async function loadAvailability(doctorId: string, date: Date) {
    const dateStr = format(date, "yyyy-MM-dd");
    const availability = await getDoctorAvailability(doctorId, dateStr);
    const slots: SlotEvent[] = availability.available_slots.map((time) => {
      const [hours, minutes] = time.split(":").map(Number);
      const start = new Date(date);
      start.setHours(hours, minutes, 0, 0);
      const end = new Date(start);
      end.setMinutes(end.getMinutes() + 20);
      return { title: "Available", start, end };
    });
    setEvents(slots);
  }

  function handleDoctorChange(doctorId: string) {
    setSelectedDoctorId(doctorId);
    loadAvailability(doctorId, new Date());
  }

  function handleNavigate(date: Date) {
    if (selectedDoctorId) loadAvailability(selectedDoctorId, date);
  }

  function handleSelectSlot(slotInfo: SlotInfo) {
    const matchingEvent = events.find((e) => e.start.getTime() === slotInfo.start.getTime());
    if (matchingEvent) setSelectedSlot(matchingEvent.start);
  }

  async function confirmBooking() {
    if (!selectedSlot || !selectedDoctorId) return;
    setBooking(true);
    setMessage("");
    try {
      const patient = await getMyPatientProfile();
      await createAppointment({
        patient_id: patient.id,
        doctor_id: selectedDoctorId,
        room_id: 1,
        scheduled_time: selectedSlot.toISOString(),
        urgency_level: Number(urgencyLevel),
      });
      setMessage("Appointment booked.");
      setSelectedSlot(null);
      loadAvailability(selectedDoctorId, selectedSlot);
    } catch {
      setMessage("Booking failed, slot may already be taken.");
    } finally {
      setBooking(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="max-w-xs">
        <Label>Doctor</Label>
        <Select value={selectedDoctorId} onValueChange={handleDoctorChange}>
          <SelectTrigger><SelectValue placeholder="Select a doctor" /></SelectTrigger>
          <SelectContent>
            {doctors.map((d) => (
              <SelectItem key={d.id} value={d.id}>{d.name} - {d.specialization}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {selectedDoctorId && (
        <div style={{ height: 500 }}>
          <Calendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            selectable
            defaultView="day"
            views={["day", "week"]}
            onNavigate={handleNavigate}
            onSelectSlot={handleSelectSlot}
            step={20}
            timeslots={1}
          />
        </div>
      )}

      {message && <p className="text-sm">{message}</p>}

      <Dialog open={!!selectedSlot} onOpenChange={(open) => !open && setSelectedSlot(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm booking</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-500">
            {selectedSlot && format(selectedSlot, "PPpp")}
          </p>
          <div className="space-y-2">
            <Label>Urgency (1-5)</Label>
            <Select value={urgencyLevel} onValueChange={setUrgencyLevel}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {[1, 2, 3, 4, 5].map((n) => (
                  <SelectItem key={n} value={String(n)}>{n}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={confirmBooking} disabled={booking}>
            {booking ? "Booking..." : "Confirm"}
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  );
}