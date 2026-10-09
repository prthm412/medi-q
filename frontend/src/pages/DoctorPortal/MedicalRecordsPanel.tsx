import { useEffect, useState } from "react";
import { getMedicalRecords, createMedicalRecord } from "@/api/medicalRecords";
import { Button } from "@/components/ui/button";
import type { MedicalRecord } from "@/types";

interface Props {
  patientId: string;
  appointmentId: string;
}

export function MedicalRecordsPanel({ patientId, appointmentId }: Props) {
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getMedicalRecords(patientId).then(setRecords);
  }, [patientId]);

  const alreadyHasRecordForThisVisit = records.some((r) => r.appointment_id === appointmentId);

  async function handleSave() {
    setSaving(true);
    setError("");
    try {
      const record = await createMedicalRecord(appointmentId, notes);
      setRecords([record, ...records]);
      setNotes("");
    } catch {
      setError("Failed to save. A record may already exist for this appointment.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {records.length === 0 && <p className="text-sm text-slate-500">No records yet.</p>}
        {records.map((r) => (
          <div key={r.id} className="border rounded p-2 text-sm">
            <p className="text-slate-500">{new Date(r.created_at).toLocaleString()}</p>
            <p>{r.notes}</p>
          </div>
        ))}
      </div>

      {!alreadyHasRecordForThisVisit && (
        <div className="space-y-2">
          <textarea
            className="w-full border rounded p-2 text-sm"
            rows={3}
            placeholder="Notes for this visit"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button onClick={handleSave} disabled={saving || !notes}>
            {saving ? "Saving..." : "Save note"}
          </Button>
        </div>
      )}
    </div>
  );
}