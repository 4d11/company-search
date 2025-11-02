export const CompanyCardSkeleton = () => {
  return (
    <div className="p-10 rounded-3xl bg-white shadow-xl border border-gray-100 animate-pulse">
      <div className="flex items-start gap-6">
        <div className="w-16 h-16 rounded-2xl bg-gray-200 flex-shrink-0"></div>
        <div className="flex-1 space-y-4">
          <div className="h-8 bg-gray-200 rounded-lg w-3/4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="h-7 w-24 bg-gray-200 rounded-full"></div>
            <div className="h-7 w-32 bg-gray-200 rounded-full"></div>
            <div className="h-7 w-20 bg-gray-200 rounded-full"></div>
            <div className="h-7 w-28 bg-gray-200 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const CompanyListSkeleton = ({ count = 3 }: { count?: number }) => {
  return (
    <div className="space-y-6">
      {Array.from({ length: count }).map((_, i) => (
        <CompanyCardSkeleton key={i} />
      ))}
    </div>
  );
};
