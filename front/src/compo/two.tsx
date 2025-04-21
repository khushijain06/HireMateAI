import  { useEffect, useState } from "react";

const HireMateResult = () => {
  const [selectedJob, setSelectedJob] = useState("All Jobs");
  const [threshold, setThreshold] = useState(50);
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<{ email:string ,title: string, name: string; similarity: number; status: string }[]>([]);
  const [jobTitles, setJobTitles] = useState<string[]>([]); // 👈 job titles
  const [emailSending, setEmailSending] = useState(false);


  const handleSendEmails = async () => {
    try {
      setEmailSending(true);
  
      const thresholdDecimal = threshold / 100; // 👈 Convert to decimal
  
      const response = await fetch(
        `https://hiremateai.onrender.com/send-mails?threshold=${thresholdDecimal}`, // ✅ Send decimal
        {
          method: "POST",
        }
      );
  
      if (response.ok) {
        alert("Emails sent successfully!");
      } else {
        alert("Failed to send emails.");
      }
    } catch (error) {
      console.error("Email sending error:", error);
      alert("An error occurred while sending emails.");
    } finally {
      setEmailSending(false);
    }
  };
  
  

  // Fetch job titles on mount
  useEffect(() => {
    const fetchJobTitles = async () => {
      try {
        const response = await fetch("https://hiremateai.onrender.com/cosine?threshold=0");
        const data = await response.json();
  
        const titles = Array.isArray(data.results)
          ? data.results.map((job: any) => job.job_title)
          : [];
  
        const uniqueTitles = [...new Set(titles)];
  
        setJobTitles(["All Jobs", ...uniqueTitles]);
      } catch (error) {
        console.error("Error fetching job titles:", error);
        alert("Failed to load job titles.");
      }
    };
  
    fetchJobTitles();
  }, []);
  

  const handleGetCandidates = async () => {
    setLoading(true);
    try {
      const thresholdDecimal = threshold / 100;
      const response = await fetch(`https://hiremateai.onrender.com/cosine?threshold=${thresholdDecimal}`);
      const data = await response.json();

      const matchedJob = data.results.find((job: any) =>
        selectedJob === "All Jobs" || job.job_title === selectedJob
      );

      if (!matchedJob) {
        alert("No results found for the selected job.");
        setCandidates([])
      } else {
        const updatedCandidates = matchedJob.matches.map((candidate: any) => ({
          name: candidate.cv_name,
          similarity: Math.round(candidate.similarity * 100),
          status: candidate.status,
          title: candidate.job_title,
          email: candidate.candidate_email 
        }));
        setCandidates(updatedCandidates)
      }
    } catch (error) {
      console.error("Error fetching cosine similarity:", error);
      alert("Failed to fetch candidates.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-6 space-y-6">
      <h1 className="text-5xl font-bold">HireMate</h1>

      {/* Job selection and threshold */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Select Job</label>
          <select
            className="bg-gray-800 border border-gray-600 px-3 py-1 rounded-md text-white"
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
          >
            {jobTitles.map((title, idx) => (
              <option key={idx} value={title}>
                {title}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Threshold: {threshold}%</span>
          <button
            onClick={() => setEditing(!editing)}
            className="bg-gray-800 border hover:cursor-pointer border-gray-600 px-3 py-1 rounded-md text-white text-sm"
          >
            {editing ? "Done" : "Edit"}
          </button>
        </div>

        {editing && (
          <input
            type="range"
            min="0"
            max="100"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="w-full hover:cursor-pointer sm:w-40"
          />
        )}
      </div>

      {/* Action Buttons */}
      <div>
        <button
          onClick={handleGetCandidates}
          className="bg-blue-500 mr-4 hover:cursor-pointer hover:bg-blue-600 text-white font-semibold py-2 px-6 rounded-lg transition disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Loading..." : "Get Candidates"}
        </button>

        <button
  onClick={handleSendEmails}
  className="mt-4 bg-blue-500 hover:cursor-pointer hover:bg-blue-600 text-white font-semibold py-2 px-6 rounded-lg transition disabled:opacity-50"
  disabled={loading || emailSending}
>
  {emailSending ? "Sending..." : "Send Selection Mail"}
</button>

      </div>

      {/* Loading indicator */}
      {loading && <div className="text-lg mt-6 animate-pulse">Fetching results, please wait...</div>}

      {/* Results Table */}
      {!loading && (
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">
            Candidates Matching: {selectedJob}
          </h2>
          <table className="min-w-[300px] w-full max-w-2xl mx-auto border border-gray-700 text-left">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="py-2 px-4">Candidate</th>
                <th className="py-2 px-4">Similarity</th>
                <th className="py-2 px-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {candidates.length === 0 ? (
                <tr>
                  <td className="py-2 px-4 text-center" colSpan={3}>
                    No candidates found.
                  </td>
                </tr>
              ) : (
                candidates.map((c, index) => (
                  <tr key={index} className="border-t border-gray-800">
                    <td className="py-2 px-4">{c.name}</td>
                    <td className="py-2 px-4">{c.similarity}%</td>
                    <td className="py-2 px-4">
                    <span
  className='px-2 py-1 rounded-full text-xs font-medium'
>
  Selected
</span>

                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default HireMateResult;
