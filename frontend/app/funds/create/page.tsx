"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { fundApi } from "@/lib/api";
import { ArrowLeft, Save } from "lucide-react";

export default function CreateFundPage() {
  const [name, setName] = useState("");
  const [gpName, setGpName] = useState("");
  const [fundType, setFundType] = useState("");
  const [vintageYear, setVintageYear] = useState<number | "">("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Fund name is required");
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const newFund = await fundApi.create({
        name: name.trim(),
        gp_name: gpName.trim() || undefined,
        fund_type: fundType.trim() || undefined,
        vintage_year: vintageYear ? Number(vintageYear) : undefined,
      });
      router.push(`/funds/${newFund.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create fund");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Create New Fund</h1>
        <button
          onClick={() => router.back()}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back</span>
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Fund Name *
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Tech Ventures Fund III"
            required
          />
        </div>

        <div>
          <label
            htmlFor="gpName"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            GP Name (Optional)
          </label>
          <input
            id="gpName"
            type="text"
            value={gpName}
            onChange={(e) => setGpName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Tech Ventures Partners"
          />
        </div>

        <div>
          <label
            htmlFor="fundType"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Fund Type (Optional)
          </label>
          <input
            id="fundType"
            type="text"
            value={fundType}
            onChange={(e) => setFundType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Venture Capital, Buyout"
          />
        </div>

        <div>
          <label
            htmlFor="vintageYear"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Vintage Year (Optional)
          </label>
          <input
            id="vintageYear"
            type="number"
            value={vintageYear}
            onChange={(e) =>
              setVintageYear(e.target.value ? Number(e.target.value) : "")
            }
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., 2023"
            min="1900"
            max="2100"
          />
        </div>

        <div className="pt-4">
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <Save className="w-4 h-4 animate-spin" />
                <span>Creating...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Create Fund</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
