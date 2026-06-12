import { Check } from "lucide-react";

export function StepIndicator({ steps, current }: { steps: string[]; current: number }) {
  return (
    <ol className="flex items-center">
      {steps.map((label, i) => {
        const step = i + 1;
        const state = step < current ? "done" : step === current ? "current" : "upcoming";
        return (
          <li key={label} className="flex flex-1 items-center last:flex-none">
            <div className="flex items-center gap-2">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  state === "done"
                    ? "bg-teal-600 text-white"
                    : state === "current"
                      ? "border-2 border-teal-600 text-teal-700"
                      : "border border-slate-300 text-slate-400"
                }`}
              >
                {state === "done" ? <Check className="h-4 w-4" /> : step}
              </span>
              <span className={`text-sm font-medium ${state === "upcoming" ? "text-slate-400" : "text-slate-900"}`}>
                {label}
              </span>
            </div>
            {step < steps.length && <span className="mx-3 h-px flex-1 bg-slate-200" />}
          </li>
        );
      })}
    </ol>
  );
}
