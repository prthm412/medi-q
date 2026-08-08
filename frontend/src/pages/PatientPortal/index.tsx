import { useAuth } from "@/context/AuthContext";
import { BookingCalendar } from "./BookingCalendar";
import { AppointmentHistory } from "./AppointmentHistory";
import { QueueWidget } from "./QueueWidget";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function PatientPortal() {
  const { logout } = useAuth();

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Patient Portal</h1>
        <Button variant="outline" onClick={logout}>Log out</Button>
      </div>

      <QueueWidget />

      <Card>
        <CardHeader>
          <CardTitle>Book an Appointment</CardTitle>
        </CardHeader>
        <CardContent>
          <BookingCalendar />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appointment History</CardTitle>
        </CardHeader>
        <CardContent>
          <AppointmentHistory />
        </CardContent>
      </Card>
    </div>
  );
}