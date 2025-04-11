import React, { useState } from "react";
import { useNavigate } from "react-router";

const HireMate = () => {
const navigate = useNavigate()
  const [jobFile, setJobFile] = useState<File | null>(null);
  const [cvFolder, setCvFolder] = useState<File[] | null>(null);
  const [load, setLoad] = useState(false);

  const handleJobChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setJobFile(e.target.files[0]);
    }
  };

  const handleCVChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const allFiles = Array.from(e.target.files);
      const pdfs = allFiles.filter(file => file.name.endsWith(".pdf"));
      setCvFolder(pdfs);
      console.log("Uploaded CV files with relative paths:");
      pdfs.forEach(file => {
        console.log(file.webkitRelativePath);
      });
    }
  };
  

  const handleSummarizeNo = async () => {
    setLoad(true);
  
    try {
      await fetch("http://127.0.0.1:8000/summarize", {
        method: "POST",
      });
      await fetch("http://127.0.0.1:8000/summarize-cvs", {
        method: "POST",
      });
      alert("Job and CVs summarized successfully!");   
    } catch (err) {
      console.error(err);
      alert("Something went wrong while summarizing!");
    } finally {  
      navigate('/candidates');
      setLoad(false);
    }
  };
  const handleSummarize = async () => {
    if (!jobFile || !cvFolder) {
      alert("Please upload both job description and CVs.");
      return;
    }

    setLoad(true);

    try {
      const jobData = new FormData();
      jobData.append("file", jobFile);
      await fetch("http://127.0.0.1:8000/summarize", {
        method: "POST",
        body: jobData,
      });

      const cvData = new FormData();
      cvFolder.forEach(file => {
        // Append files with their relative path as key, optional
        cvData.append("files", file, file.webkitRelativePath || file.name);
      });
      
      await fetch("http://127.0.0.1:8000/summarize-cvs", {
        method: "POST",
        body: cvData,
      });

     
    } catch (err) {
      console.error(err);
      alert("Something went wrong while summarizing!");
    } finally {
      setLoad(false); 
      alert("Job and CVs summarized successfully!");
      navigate('./candidates')
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center px-4">
      <h1 className="text-5xl font-bold mb-4">HireMate</h1>
      <p className="text-lg mb-8 text-gray-400 text-center">
        Upload the job description CSV file and a folder of CVs.
      </p>

      <div className="flex flex-col md:flex-row gap-6">
        {/* Upload Section */}
        <div className="border border-gray-700 rounded-xl p-6 w-80 bg-gray-800">
          <h2 className="text-xl font-semibold mb-4">Upload your data</h2>
          <div className="mb-4">
            <label className="block mb-1">Job description (.csv)</label>
            <input
              type="file"
              accept=".csv"
              onChange={handleJobChange}
              className="block w-full text-sm text-gray-300
                         file:mr-4 file:py-2 file:px-4
                         file:rounded-lg file:border-0
                         file:text-sm file:font-semibold
                         file:bg-gray-700 file:text-white
                         hover:file:bg-gray-600"
            />
          </div>
          <div>
            <label className="block mb-1">CV folder</label>
            <input
  type="file"
  multiple
  onChange={handleCVChange}
  className="block w-full text-sm text-gray-300
             file:mr-4 file:py-2 file:px-4
             file:rounded-lg file:border-0
             file:text-sm file:font-semibold
             file:bg-gray-700 file:text-white
             hover:file:bg-gray-600 mb-4"
  ref={(input) => {
    if (input) {
      input.setAttribute("webkitdirectory", ""); // important for Chrome
      input.setAttribute("directory", "");        // some support in Firefox
    }
  }}
/>

          </div>

          <button
            className="w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 hover:cursor-pointer rounded-lg text-white font-semibold transition"
            onClick={handleSummarize}
          >
            Summarize
          </button>
        </div>

        {/* Default Dataset Section */}
        <div className="border border-gray-700 rounded-xl p-6 w-80 bg-gray-800">
          <h2 className="text-xl font-semibold mb-4">Use default dataset</h2>
          <button
            className="w-full py-2 px-4 bg-blue-500 hover:bg-blue-600 hover:cursor-pointer rounded-lg text-white font-semibold transition"
            onClick={handleSummarizeNo}
          >
            Summarize
          </button>
        </div>
      </div>

      {/* Loading Section */}
      {load && (
        <div className="mt-8 px-6 py-4 bg-gray-800 rounded-lg shadow-lg text-center w-full max-w-md">
          <p className="text-xl text-blue-400 animate-pulse font-semibold">
            Summarizing... Please wait ⏳
          </p>
        </div>
      )}
    </div>
  );
};

export default HireMate;
