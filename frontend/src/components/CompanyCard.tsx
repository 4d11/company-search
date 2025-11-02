import { Company } from "../types";

interface CompanyCardProps {
  company: Company;
}

export const CompanyCard = ({ company }: CompanyCardProps) => {
  return (
    <div className="p-10 rounded-3xl bg-white shadow-xl border border-gray-100 hover:shadow-2xl transition-all duration-300 hover:scale-[1.005]">
      <div className="flex items-start gap-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0 shadow-md">
          {company.company_name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1">
          <h3 className="text-3xl font-bold text-gray-900 mb-4">
            {company.company_name}
          </h3>
          {company.explanation && (
            <div className="mb-5 p-4 rounded-2xl bg-blue-50 border-2 border-blue-200">
              <p className="text-sm font-bold text-blue-900 mb-2 flex items-center gap-2">
                <span className="text-base">✨</span>
                Why this company?
              </p>
              <p className="text-sm text-blue-800 leading-relaxed">
                {company.explanation}
              </p>
            </div>
          )}
          {company.description && (
            <p className="text-gray-600 mb-6 text-base leading-relaxed">
              {company.description}
            </p>
          )}
          <div className="flex flex-wrap gap-2 items-center">
            {company.industries && company.industries.length > 0 && (
              <>
                {company.industries.map((industry, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-50 text-purple-700 text-sm font-medium border border-purple-200">
                    🏢 {industry}
                  </span>
                ))}
              </>
            )}

            {company.target_markets && company.target_markets.length > 0 && (
              <>
                {company.target_markets.map((market, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-teal-50 text-teal-700 text-sm font-medium border border-teal-200">
                    🎯 {market}
                  </span>
                ))}
              </>
            )}

            {company.stage && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-50 text-amber-700 text-sm font-medium border border-amber-200">
                🚀 {company.stage}
              </span>
            )}

            {company.funding_amount && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-50 text-green-700 text-sm font-medium border border-green-200">
                💰 ${(company.funding_amount / 1000000).toFixed(1)}M
              </span>
            )}

            {company.employee_count && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-50 text-indigo-700 text-sm font-medium border border-indigo-200">
                👥 {company.employee_count} employees
              </span>
            )}

            {(company.location || company.city) && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-50 text-blue-700 text-sm font-medium border border-blue-200">
                📍 {company.location || company.city}
              </span>
            )}

            {company.website_url && (
              <a
                href={company.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gray-100 text-gray-700 text-sm font-medium hover:bg-gray-200 transition-colors border border-gray-200"
              >
                🔗 Website
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
