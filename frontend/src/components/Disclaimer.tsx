export function NonAdviceNote({ className = "" }: { className?: string }) {
  return (
    <p className={`text-xs text-slate-400 ${className}`}>
      Product information is provided for reference only and is not medical advice. Consult a
      pharmacist or doctor with questions about any medication.
    </p>
  );
}
