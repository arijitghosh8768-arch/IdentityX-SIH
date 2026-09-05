import { useState, useRef, useEffect } from 'react'

function App() {
  const [currentTab, setCurrentTab] = useState("scanner");
  
  const [riskScore, setRiskScore] = useState(null);
  const [results, setResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const [documentFile, setDocumentFile] = useState(null);
  const [liveFaceFile, setLiveFaceFile] = useState(null);
  
  const [docPreview, setDocPreview] = useState(null);
  const [facePreview, setFacePreview] = useState(null);

  // Webcam states
  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const docInputRef = useRef();
  const faceInputRef = useRef();

  const handleFileChange = (e, setFile, setPreview) => {
    const file = e.target.files[0];
    if (file) {
      setFile(file);
      setPreview(URL.createObjectURL(file));
      setIsWebcamActive(false); 
    }
  };

  const startWebcam = async () => {
    setIsWebcamActive(true);
    setFacePreview(null);
    setLiveFaceFile(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Error accessing webcam:", err);
      alert("Could not access webcam. Please allow permissions.");
      setIsWebcamActive(false);
    }
  };

  const captureWebcam = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      canvas.toBlob((blob) => {
        const file = new File([blob], "webcam_capture.jpg", { type: "image/jpeg" });
        setLiveFaceFile(file);
        setFacePreview(URL.createObjectURL(file));
      }, 'image/jpeg');

      const stream = video.srcObject;
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
      setIsWebcamActive(false);
    }
  };

  const analyzeDocument = async () => {
    if (!documentFile) {
      alert("Please upload a document first!");
      return;
    }

    setIsAnalyzing(true);
    
    const formData = new FormData();
    formData.append("document", documentFile);
    if (liveFaceFile) {
      formData.append("live_face", liveFaceFile);
    }

    try {
      const response = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      setResults(data);
      setRiskScore(data.risk_score);
    } catch (error) {
      console.error("Error analyzing document:", error);
      alert("Failed to connect to the analysis engine.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="min-h-screen bg-slate-100 p-8 font-sans text-slate-800 print:bg-white print:p-0">
      <div className="max-w-6xl mx-auto">
        
        {/* Header - Hidden in Print */}
        <header className="bg-white rounded-t-xl shadow-sm border-b p-6 flex justify-between items-center print:hidden">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-indigo-900">IDENTITY<span className="text-indigo-500">X</span></h1>
            <p className="text-sm text-slate-500 mt-1">AI Document Screening Platform</p>
          </div>
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setCurrentTab("scanner")}
              className={`font-bold px-4 py-2 rounded-lg ${currentTab === "scanner" ? "bg-indigo-100 text-indigo-700" : "text-slate-500 hover:bg-slate-100"}`}
            >
              Scanner
            </button>
            <button 
              onClick={() => setCurrentTab("admin")}
              className={`font-bold px-4 py-2 rounded-lg ${currentTab === "admin" ? "bg-indigo-100 text-indigo-700" : "text-slate-500 hover:bg-slate-100"}`}
            >
              Admin Dashboard
            </button>
            <div className="h-8 border-l border-slate-300 mx-2"></div>
            <div className="flex items-center gap-2 bg-slate-50 px-4 py-2 rounded-lg border border-slate-200">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-semibold text-slate-700">Officer Session</span>
            </div>
          </div>
        </header>

        {/* ADMIN TAB */}
        {currentTab === "admin" && (
          <main className="bg-white shadow-lg rounded-b-xl p-8 border-x border-b border-slate-200 animate-fade-in">
             <h2 className="text-2xl font-bold mb-6">System Analytics (Mocked Data)</h2>
             
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
               <div className="bg-indigo-50 p-6 rounded-xl border border-indigo-100">
                  <h3 className="text-sm font-bold text-indigo-400 tracking-wider">TOTAL SCANNED</h3>
                  <p className="text-4xl font-black text-indigo-900 mt-2">1,248</p>
               </div>
               <div className="bg-red-50 p-6 rounded-xl border border-red-100">
                  <h3 className="text-sm font-bold text-red-400 tracking-wider">TAMPERED FLAGS</h3>
                  <p className="text-4xl font-black text-red-900 mt-2">32</p>
               </div>
               <div className="bg-green-50 p-6 rounded-xl border border-green-100">
                  <h3 className="text-sm font-bold text-green-400 tracking-wider">AVERAGE RISK</h3>
                  <p className="text-4xl font-black text-green-900 mt-2">14/100</p>
               </div>
             </div>
             
             <div className="w-full h-[400px] bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-center text-slate-400">
                [ Chart Placeholder: Daily Scan Volume ]
             </div>
          </main>
        )}

        {/* SCANNER TAB */}
        {currentTab === "scanner" && (
          <main className="bg-white shadow-lg rounded-b-xl p-8 border-x border-b border-slate-200 print:shadow-none print:border-none print:p-0">
            
            {/* Upload Section - Hidden in Print */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8 print:hidden">
              {/* Document Section */}
              <div 
                className="border-2 border-dashed border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center bg-slate-50 min-h-[300px] cursor-pointer hover:bg-slate-100 transition relative"
                onClick={() => docInputRef.current.click()}
              >
                <span className="text-slate-400 font-semibold mb-4 tracking-wider">DOCUMENT</span>
                <input type="file" ref={docInputRef} className="hidden" accept="image/*,application/pdf" onChange={(e) => handleFileChange(e, setDocumentFile, setDocPreview)} />
                
                {docPreview ? (
                  documentFile?.type === "application/pdf" ? (
                    <div className="w-full max-w-sm aspect-[4/3] bg-red-50 rounded shadow-sm border border-red-200 flex flex-col items-center justify-center text-red-400">
                      <span className="text-4xl mb-2">📄</span>
                      <span className="text-sm font-bold text-red-600">{documentFile.name}</span>
                      <span className="text-xs mt-1">PDF Selected</span>
                    </div>
                  ) : (
                    <img src={docPreview} alt="Document" className="max-w-full max-h-[250px] object-contain rounded shadow-sm border" />
                  )
                ) : (
                  <div className="w-full max-w-sm aspect-[4/3] bg-white rounded shadow-sm border flex flex-col items-center justify-center text-slate-300">
                    <span className="text-4xl mb-2">📄</span>
                    <span className="text-sm">Click to upload Passport (Image/PDF)</span>
                  </div>
                )}
              </div>

              {/* Live Face Section */}
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-6 flex flex-col items-center justify-center bg-slate-50 min-h-[300px] relative">
                <span className="text-slate-400 font-semibold mb-4 tracking-wider">LIVE FACE (Optional)</span>
                
                <div className="flex-grow flex items-center justify-center w-full">
                  {isWebcamActive ? (
                    <div className="flex flex-col items-center gap-4">
                      <video ref={videoRef} autoPlay playsInline className="w-48 h-48 object-cover rounded-full shadow-sm border-4 border-indigo-200 bg-black"></video>
                      <canvas ref={canvasRef} className="hidden"></canvas>
                      <button onClick={captureWebcam} className="bg-indigo-600 text-white px-4 py-2 rounded-full text-sm font-bold hover:bg-indigo-700">
                        📸 Capture
                      </button>
                    </div>
                  ) : facePreview ? (
                    <div className="flex flex-col items-center gap-4 cursor-pointer" onClick={() => faceInputRef.current.click()}>
                      <img src={facePreview} alt="Live Face" className="w-48 h-48 object-cover rounded-full shadow-sm border-4 border-white" />
                      <span className="text-xs text-slate-400">Click to change</span>
                    </div>
                  ) : (
                    <div className="w-48 h-48 bg-white rounded-full shadow-sm border flex flex-col items-center justify-center text-slate-300">
                      <span className="text-5xl mb-2">👤</span>
                      <span className="text-xs">No Face</span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                {!isWebcamActive && (
                  <div className="flex gap-4 mt-6">
                    <input type="file" ref={faceInputRef} className="hidden" accept="image/*" onChange={(e) => handleFileChange(e, setLiveFaceFile, setFacePreview)} />
                    <button onClick={() => faceInputRef.current.click()} className="bg-white border border-slate-300 text-slate-600 px-4 py-2 rounded-lg text-sm font-semibold hover:bg-slate-50">
                      📁 Upload File
                    </button>
                    <button onClick={startWebcam} className="bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-slate-700">
                      📷 Open Camera
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-center mb-10 print:hidden">
              <button 
                onClick={analyzeDocument}
                disabled={isAnalyzing}
                className={`font-bold py-4 px-12 rounded-full shadow-lg transition transform text-lg text-white ${isAnalyzing ? 'bg-indigo-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 hover:-translate-y-1'}`}
              >
                {isAnalyzing ? '[ ANALYZING... ]' : '[ ANALYZE DOCUMENT ]'}
              </button>
            </div>

            {results && (
              <div className="print:block">
                
                {/* Print Header */}
                <div className="hidden print:block mb-8 border-b-2 border-slate-800 pb-4">
                  <h1 className="text-4xl font-extrabold tracking-tight text-slate-900">IDENTITY<span className="text-slate-500">X</span></h1>
                  <h2 className="text-xl font-bold mt-2">OFFICIAL VERIFICATION REPORT</h2>
                  <p className="text-slate-500">Generated on {new Date().toLocaleString()}</p>
                </div>

                <div className="flex justify-between items-center mb-6 print:hidden">
                  <h2 className="text-2xl font-bold text-slate-800">Analysis Results</h2>
                  <button onClick={handlePrint} className="bg-slate-800 hover:bg-slate-700 text-white px-6 py-2 rounded-lg font-bold shadow-md flex items-center gap-2">
                    📄 Download PDF Report
                  </button>
                </div>
                
                <hr className="my-8 border-slate-200 print:hidden" />
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 animate-fade-in">
                  
                  {/* Modules Status */}
                  <div className="space-y-4">
                    <h3 className="text-lg font-bold text-slate-800 mb-6">Verification Modules</h3>
                    
                    <div className={`flex justify-between items-center p-3 rounded-lg border ${results.ocr?.status === 'success' ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                      <span className="font-semibold text-slate-700">OCR Extraction</span>
                      <span className={`${results.ocr?.status === 'success' ? 'text-green-600' : 'text-red-600'} font-bold flex items-center gap-2`}>
                        {results.ocr?.status === 'success' ? '✓ SUCCESS' : '❌ FAILED'}
                      </span>
                    </div>
                    
                    <div className={`flex justify-between items-center p-3 rounded-lg border ${results.validation?.mrz_mismatches?.length === 0 ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                      <span className="font-semibold text-slate-700">MRZ Consistency</span>
                      <span className={`${results.validation?.mrz_mismatches?.length === 0 ? 'text-green-600' : 'text-red-600'} font-bold flex items-center gap-2`}>
                        {results.validation?.mrz_mismatches?.length === 0 ? '✓ VALID' : '⚠ MISMATCH'}
                      </span>
                    </div>
                    
                    <div className={`flex justify-between items-center p-3 rounded-lg border ${results.validation?.status === 'VALID' ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                      <span className="font-semibold text-slate-700">Document Checks</span>
                      <span className={`${results.validation?.status === 'VALID' ? 'text-green-600' : 'text-red-600'} font-bold flex items-center gap-2`}>
                        {results.validation?.status === 'VALID' ? '✓ VALID' : '⚠ SUSPICIOUS'}
                      </span>
                    </div>
                    
                    <div className={`flex justify-between items-center p-3 rounded-lg border ${results.tampering?.is_tampered ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'}`}>
                      <span className="font-semibold text-slate-700">Tampering (ELA)</span>
                      <span className={`${results.tampering?.is_tampered ? 'text-red-600' : 'text-green-600'} font-bold flex items-center gap-2`}>
                        {results.tampering?.is_tampered ? `⚠ ${results.tampering?.tamper_score}% SUSPICIOUS` : '✓ GENUINE'}
                      </span>
                    </div>
                    
                    {liveFaceFile && (
                      <div className={`flex justify-between items-center p-3 rounded-lg border ${results.face_match?.match ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                        <span className="font-semibold text-slate-700">Face Match</span>
                        <span className={`${results.face_match?.match ? 'text-green-600' : 'text-red-600'} font-bold flex items-center gap-2`}>
                          {results.face_match?.match ? `✓ ${results.face_match?.similarity}% MATCH` : '❌ MISMATCH'}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Risk Score */}
                  <div className="flex flex-col items-center justify-center p-8 bg-slate-50 rounded-2xl border border-slate-200 shadow-inner relative">
                    <h3 className="text-sm font-bold text-slate-400 tracking-widest mb-4">OVERALL RISK SCORE</h3>
                    
                    <div className={`text-7xl font-black mb-2 drop-shadow-sm ${riskScore > 50 ? 'text-red-600' : riskScore > 20 ? 'text-yellow-600' : 'text-green-600'}`}>
                      {riskScore} <span className="text-3xl text-slate-400">/ 100</span>
                    </div>
                    
                    <div className={`px-6 py-2 font-bold rounded-full text-lg mb-8 ${riskScore > 50 ? 'bg-red-100 text-red-700 animate-pulse' : riskScore > 20 ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                      {riskScore > 50 ? '🔴 HIGH RISK' : riskScore > 20 ? '🟡 MEDIUM RISK' : '🟢 LOW RISK'}
                    </div>

                    {riskScore > 20 && (
                      <div className="w-full bg-white p-5 rounded-xl border border-slate-200 text-left">
                        <h4 className="font-bold text-slate-700 mb-2">Primary Reasons:</h4>
                        <ul className="text-sm text-slate-600 space-y-2">
                          {results.validation?.warnings?.map((warn, i) => <li key={i} className="flex gap-2 text-red-500"><span>⚠</span> {warn}</li>)}
                          {results.validation?.mrz_mismatches?.map((mm, i) => <li key={i} className="flex gap-2 text-red-500"><span>⚠</span> {mm}</li>)}
                          {results.tampering?.is_tampered && <li className="flex gap-2 text-red-500"><span>⚠</span> Visual tampering detected</li>}
                          {results.face_match?.match === false && <li className="flex gap-2 text-red-500"><span>⚠</span> Identity mismatch</li>}
                        </ul>
                      </div>
                    )}
                  </div>

                </div>

                {/* NEW: Visual Heatmap Output */}
                {results.tampering?.heatmap_image && (
                  <div className="mt-8 p-6 bg-red-50 border-2 border-red-200 rounded-xl">
                     <h3 className="text-lg font-bold text-red-800 mb-2">⚠ Suspicious Regions Detected</h3>
                     <p className="text-sm text-red-600 mb-4">Error Level Analysis indicates potential manipulation in the highlighted areas.</p>
                     <img src={results.tampering.heatmap_image} alt="Tampering Heatmap" className="w-full max-w-2xl mx-auto rounded-lg shadow-lg border-2 border-red-500" />
                  </div>
                )}

                {/* Blockchain Audit Trail */}
                {results.audit && (
                  <div className="mt-8 bg-slate-800 text-slate-300 p-6 rounded-2xl shadow-lg border border-slate-700 font-mono text-sm animate-fade-in print:bg-slate-100 print:text-black print:border-black">
                    <div className="flex justify-between items-center mb-4 border-b border-slate-600 pb-2 print:border-slate-300">
                      <h3 className="text-lg font-bold text-white print:text-black flex items-center gap-2">
                        <span>🔗</span> BLOCKCHAIN AUDIT TRAIL
                      </h3>
                      <span className="bg-green-500 text-black px-3 py-1 rounded-full text-xs font-bold tracking-widest flex items-center gap-2">
                        <span className="w-2 h-2 bg-black rounded-full print:hidden"></span>
                        {results.audit.blockchain_status}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-slate-500 print:text-slate-600">Report ID</p>
                        <p className="font-bold text-white print:text-black break-all">{results.audit.report_id}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 print:text-slate-600">Timestamp</p>
                        <p className="text-white print:text-black">{results.audit.timestamp}</p>
                      </div>
                      <div className="md:col-span-2">
                        <p className="text-slate-500 print:text-slate-600">Document Hash (SHA-256)</p>
                        <p className="text-slate-400 print:text-slate-700 break-all select-all">{results.audit.document_hash}</p>
                      </div>
                      <div className="md:col-span-2">
                        <p className="text-slate-500 print:text-slate-600">Transaction ID</p>
                        <p className="text-indigo-400 print:text-black break-all select-all cursor-pointer">
                          {results.audit.transaction_id}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </main>
        )}
      </div>
    </div>
  )
}

export default App
