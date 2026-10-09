import { useAuth } from "@/context/AuthContext";
import { TodaysSchedule } from "./TodaysSchedule";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function DoctorPortal() {
  const { logout } = useAuth();

  return (
    <div className="max-w-5xl mx-auto p-8 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Doctor Portal</h1>
        <Button variant="outline" onClick={logout}>Log out</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Today's Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <TodaysSchedule />
        </CardContent>
      </Card>
    </div>
  );
}