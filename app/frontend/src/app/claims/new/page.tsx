"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api, Policy } from "@/services/api";

const CLAIM_TYPES = [
  "COLLISION",
  "PROPERTY_DAMAGE",
  "MEDICAL",
  "THEFT",
  "WEATHER",
  "LIABILITY",
  "OTHER",
];

export default function NewClaimPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loadingPolicies, setLoadingPolicies] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [form, setForm] = useState({
    policy_id: "",
    incident_date: "",
    claim_type: "COLLISION",
    description: "",
    amount_requested: "",
  });

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>("");

  useEffect(() => {
    async function loadPolicies() {
      try {
        const data = await api.getPolicies({ status: "ACTIVE", limit: 100 });
        setPolicies(data);
      } catch {
        // Non-fatal
      } finally {
        setLoadingPolicies(false);
      }
    }
    loadPolicies();
  }, []);

  function handleChange(
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      // Upload document if selected
      let uploadedFileKey: string | null = null;
      if (selectedFile) {
        setUploadStatus("Requesting upload URL...");
        const presignData = await api.presignDocument({
          file_name: selectedFile.name,
          document_type: "CLAIM_EVIDENCE",
          content_type: selectedFile.type || "application/octet-stream",
        });

        setUploadStatus("Uploading document to secure storage...");
        await fetch(presignData.upload_url, {
          method: "PUT",
          body: selectedFile,
          headers: { "Content-Type": selectedFile.type || "application/octet-stream" },
        });
        uploadedFileKey = presignData.file_key;
        setUploadStatus("Document uploaded successfully.");
      }

      // File the claim
      const claim = await api.createClaim({
        policy_id: form.policy_id,
        incident_date: form.incident_date,
        claim_type: form.claim_type,
        description: form.description,
        amount_requested: parseFloat(form.amount_requested),
      });

      // Register document if uploaded
      if (uploadedFileKey && selectedFile) {
        await api.registerDocument({
          file_key: uploadedFileKey,
          file_name: selectedFile.name,
          document_type: "CLAIM_EVIDENCE",
          claim_id: claim.id,
        });
      }

      setSuccessMessage(
        `Claim ${claim.claim_number} filed successfully. You will be notified as it is processed.`
      );
      setTimeout(() => router.push("/claims"), 2500);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          "Failed to file claim. Please check your inputs and try again."
      );
    } finally {
      setSubmitting(false);
      setUploadStatus("");
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">File New Claim</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Submit a new insurance claim for processing by an an adjuster.
        </p>
      </div>

      {successMessage && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 rounded-md px-4 py-3 text-sm">
          {successMessage}
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 rounded-md px-4 py-3 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card p-6 space-y-5">
        {/* Policy selection */}
        <div>
          <label className="label" htmlFor="policy_id">
            Policy <span className="text-red-500">*</span>
          </label>
          <select
            id="policy_id"
            name="policy_id"
            className="input-field"
            value={form.policy_id}
            onChange={handleChange}
            required
            disabled={loadingPolicies}
          >
            <option value="">
              {loadingPolicies ? "Loading policies..." : "Select a policy"}
            </option>
            {policies.map((p) => (
              <option key={p.id} value={p.id}>
                {p.policy_number} — {p.policy_type} (Coverage:{" "}
                {new Intl.NumberFormat("en-US", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0,
                }).format(parseFloat(String(p.coverage_amount)))}
                )
              </option>
            ))}
          </select>
        </div>

        {/* Incident date */}
        <div>
          <label className="label" htmlFor="incident_date">
            Incident Date <span className="text-red-500">*</span>
          </label>
          <input
            id="incident_date"
            name="incident_date"
            type="date"
            className="input-field"
            value={form.incident_date}
            onChange={handleChange}
            required
            max={new Date().toISOString().split("T")[0]}
          />
        </div>

        {/* Claim type */}
        <div>
          <label className="label" htmlFor="claim_type">
            Claim Type <span className="text-red-500">*</span>
          </label>
          <select
            id="claim_type"
            name="claim_type"
            className="input-field"
            value={form.claim_type}
            onChange={handleChange}
            required
          >
            {CLAIM_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="label" htmlFor="description">
            Description <span className="text-red-500">*</span>
          </label>
          <textarea
            id="description"
            name="description"
            className="input-field min-h-[100px] resize-y"
            value={form.description}
            onChange={handleChange}
            required
            minLength={20}
            placeholder="Please describe the incident in detail, including date, location, and circumstances."
          />
          <p className="text-xs text-gray-400 mt-1">Minimum 20 characters required.</p>
        </div>

        {/* Amount requested */}
        <div>
          <label className="label" htmlFor="amount_requested">
            Amount Requested (USD) <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
            <input
              id="amount_requested"
              name="amount_requested"
              type="number"
              min="1"
              step="0.01"
              className="input-field pl-7"
              value={form.amount_requested}
              onChange={handleChange}
              required
              placeholder="0.00"
            />
          </div>
        </div>

        {/* Document upload */}
        <div>
          <label className="label">Supporting Document (optional)</label>
          <div
            className="border-2 border-dashed border-gray-300 rounded-md p-6 text-center cursor-pointer hover:border-brand-red transition-colors"
            onClick={() => fileInputRef.current?.click()}
          >
            {selectedFile ? (
              <div className="text-sm text-gray-700">
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-gray-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
              </div>
            ) : (
              <div className="text-sm text-gray-400">
                <p>Click to select a file, or drag and drop</p>
                <p className="text-xs mt-1">PDF, JPEG, PNG up to 10 MB</p>
              </div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileChange}
            className="hidden"
          />
          {uploadStatus && (
            <p className="text-xs text-blue-600 mt-1">{uploadStatus}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={submitting}
            className="btn-primary flex-1"
          >
            {submitting ? "Submitting..." : "Submit Claim"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
