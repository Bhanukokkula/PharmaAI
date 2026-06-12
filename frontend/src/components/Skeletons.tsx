export function ProductCardSkeleton() {
  return (
    <div className="flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="h-32 animate-pulse bg-slate-100" />
      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="h-4 w-20 animate-pulse rounded-full bg-slate-100" />
        <div className="h-4 w-3/4 animate-pulse rounded bg-slate-100" />
        <div className="h-3 w-1/2 animate-pulse rounded bg-slate-100" />
        <div className="mt-3 flex items-center justify-between">
          <div className="h-5 w-12 animate-pulse rounded bg-slate-100" />
          <div className="h-8 w-16 animate-pulse rounded-full bg-slate-100" />
        </div>
      </div>
    </div>
  );
}

export function ProductCardSkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}
