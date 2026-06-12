import { AlertTriangle } from "lucide-react";

export function WarningsPanel({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
      <div className="flex items-center gap-2 text-amber-800">
        <AlertTriangle className="h-4 w-4" />
        <h2 className="font-display text-sm font-semibold">Warnings</h2>
      </div>
      <p className="mt-2 whitespace-pre-line text-sm text-amber-900">{text}</p>
    </div>
  );
}
