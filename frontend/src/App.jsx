import { useState, useRef, useEffect } from 'react'
import {
  Fingerprint, ScanLine, Upload, Camera, Link2, Printer,
  CheckCircle2, XCircle, AlertTriangle, Radar,
  FileText, RotateCcw
} from 'lucide-react'

const FONT_IMPORT = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap');
  .ix-display { font-family: 'Space Grotesk', sans-serif; }
  .ix-mono { font-family: 'IBM Plex Mono', monospace; }
  .ix-body { font-family: 'Inter', sans-serif; }
  .ix-grid-bg {
    background-image:
      linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
    background-size: 32px 32px;
  }
  .ix-corner { position: relative; }
  .ix-corner::before, .ix-corner::after,
  .ix-corner > .ix-c2::before, .ix-corner > .ix-c2::after {
    content: ''; position: absolute; width: 18px; height: 18px;
    border-color: #0D9488; transition: border-color .25s ease;
  }
  .ix-corner::before { top: -1px; left: -1px; border-top: 2px solid; border-left: 2px solid; }
  .ix-corner::after { top: -1px; right: -1px; border-top: 2px solid; border-right: 2px solid; }
  .ix-corner > .ix-c2::before { bottom: -1px; left: -1px; border-bottom: 2px solid; border-left: 2px solid; position: absolute; }
  .ix-corner > .ix-c2::after { bottom: -1px; right: -1px; border-bottom: 2px solid; border-right: 2px solid; position: absolute; }
  .ix-corner.ix-idle::before, .ix-corner.ix-idle::after,
  .ix-corner.ix-idle > .ix-c2::before, .ix-corner.ix-idle > .ix-c2::after { border-color: #CBD5E1; }
  @keyframes ix-scan { 0% { transform: translateY(0); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateY(230px); opacity: 0; } }
  .ix-scanline { animation: ix-scan 1.6s linear infinite; }
  @media print {
    .ix-print-report { color: #0F172A !important; }
  }
`;

function Meter({ value }) {
  const color = value > 50 ? '#E11D48' : value > 20 ? '#D97706' : '#0D9488';
  return (
    <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{ width: `${Math.min(value, 100)}%`, backgroundColor: color }}
      />
    </div>
  );
}

function PipelineRow({ label, ok, okText, badText, warn }) {
  const state = ok ? 'ok' : warn ? 'warn' : 'bad';
  const color = state === 'ok' ? '#0D9488' : state === 'warn' ? '#D97706' : '#E11D48';
  const Icon = state === 'ok' ? CheckCircle2 : state === 'warn' ? AlertTriangle : XCircle;
  return (
    <div className="flex items-center justify-between py-3 border-b border-slate-100 last:border-b-0">
      <span className="text-sm font-medium text-slate-600 ix-body">{label}</span>
      <span className="flex items-center gap-1.5 text-xs font-semibold ix-mono" style={{ color }}>
        <Icon size={15} strokeWidth={2.25} />
        {ok ? okText : badText}
      </span>
    </div>
  );
}

function App() {
  const [currentTab, setCurrentTab] = useState("scanner");

  const [riskScore, setRiskScore] = useState(null);
  const [dashboardSummary, setDashboardSummary] = useState({
    total_scanned: 0,
    tampered_flags: 0,
    average_risk: 0
  });
  const [results, setResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [documentFile, setDocumentFile] = useState(null);
  const [documentType, setDocumentType] = useState('passport');
  const [liveFaceFile, setLiveFaceFile] = useState(null);

  const [docPreview, setDocPreview] = useState(null);
  const [facePreview, setFacePreview] = useState(null);

  const [isWebcamActive, setIsWebcamActive] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const docInputRef = useRef();
  const faceInputRef = useRef();

  useEffect(() => {
    const loadLatestInspection = async () => {
      try {
        const response = await fetch("http://localhost:8000/api/history");
        if (!response.ok) return;
        const data = await response.json();
        if (data.summary) setDashboardSummary(data.summary);
        const latest = data.items?.[0];
        if (latest) {
          setDocumentType(latest.document_type);
          setResults({
            ...latest,
            ocr: { status: latest.ocr?.status, extracted_fields: latest.extracted_fields }
          });
          setRiskScore(latest.risk_score);
        }
      } catch (error) {
        console.error("Could not load saved inspections:", error);
      }
    };

    loadLatestInspection();
  }, []);

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
    formData.append("document_type", documentType);
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

  const linked = Boolean(documentFile && liveFaceFile);

  return (
    <div className="min-h-screen bg-slate-50 ix-grid-bg ix-body text-slate-800 print:bg-white">
      <style>{FONT_IMPORT}</style>

      <div className="max-w-6xl mx-auto px-4 md:px-8 py-8 space-y-8">

        {/* Header */}
        <header className="flex flex-col md:flex-row gap-5 justify-between md:items-center bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm print:hidden">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600">
              <Fingerprint size={22} strokeWidth={2} />
            </div>
            <div>
              <h1 className="ix-display text-xl font-bold tracking-tight text-slate-900 leading-none">
                IdentityX
              </h1>
              <p className="text-xs text-slate-500 mt-1">Document and biometric inspection console</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <nav className="flex items-center gap-6">
              <button
                onClick={() => setCurrentTab("scanner")}
                className={`relative text-sm font-semibold pb-1 transition-colors ${currentTab === "scanner" ? "text-teal-600" : "text-slate-500 hover:text-slate-800"}`}
              >
                Scanner
                {currentTab === "scanner" && <span className="absolute left-0 right-0 -bottom-[20px] h-[2px] bg-teal-600 rounded-full" />}
              </button>
              <button
                onClick={() => setCurrentTab("admin")}
                className={`relative text-sm font-semibold pb-1 transition-colors ${currentTab === "admin" ? "text-teal-600" : "text-slate-500 hover:text-slate-800"}`}
              >
                Dashboard
                {currentTab === "admin" && <span className="absolute left-0 right-0 -bottom-[20px] h-[2px] bg-teal-600 rounded-full" />}
              </button>
            </nav>
            <div className="flex items-center gap-2 pl-6 border-l border-slate-200">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
              </span>
              <span className="text-xs font-medium text-slate-600">Officer session active</span>
            </div>
          </div>
        </header>

        {/* ADMIN TAB */}
        {currentTab === "admin" && (
          <main className="space-y-6">
            <div className="flex justify-between items-baseline">
              <h2 className="ix-display text-lg font-bold text-slate-900">System analytics</h2>
              <span className="text-xs ix-mono text-slate-400">sample data stream</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total scanned</h3>
                    <p className="ix-display text-3xl font-bold text-slate-900 mt-2">{dashboardSummary.total_scanned}</p>
              </div>
              <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Tampered flags</h3>
                    <p className="ix-display text-3xl font-bold text-rose-600 mt-2">{dashboardSummary.tampered_flags}</p>
              </div>
              <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Average risk</h3>
                    <p className="ix-display text-3xl font-bold text-teal-600 mt-2">{dashboardSummary.average_risk}<span className="text-base text-slate-400 font-normal"> / 100</span></p>
              </div>
            </div>

            {results ? (
              <section className="bg-white rounded-xl border border-slate-200/80 shadow-sm p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
                  <div>
                    <h3 className="ix-display text-base font-bold text-slate-900">Latest inspection</h3>
                    <p className="text-xs text-slate-500 mt-1">
                      {documentType.replaceAll('_', ' ')}{documentFile ? ` · ${documentFile.name}` : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs ix-mono">
                    <span className="text-slate-400">risk</span>
                    <span className="font-bold text-teal-600">{riskScore ?? 0}/100</span>
                    <span className="px-2 py-1 rounded border border-slate-200 text-slate-600">
                      {results.validation?.status || 'UNKNOWN'}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-6">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
                    {Object.entries(results.ocr?.extracted_fields || {}).map(([field, value]) => (
                      <div key={field} className="flex justify-between gap-4 border-b border-slate-100 pb-2 text-sm">
                        <span className="text-slate-400 capitalize">{field.replaceAll('_', ' ')}</span>
                        <span className="text-right font-semibold text-slate-700 break-all">{value || 'Not detected'}</span>
                      </div>
                    ))}
                  </div>

                  <div className="lg:w-56 border-l border-slate-100 pl-6 space-y-3 text-xs">
                    <div className="flex justify-between gap-4"><span className="text-slate-400">OCR</span><span className="font-semibold text-slate-700">{results.ocr?.status || '—'}</span></div>
                    <div className="flex justify-between gap-4"><span className="text-slate-400">MRZ</span><span className="font-semibold text-slate-700">{results.mrz?.status || '—'}</span></div>
                    <div className="flex justify-between gap-4"><span className="text-slate-400">Tampering</span><span className="font-semibold text-slate-700">{results.tampering?.tamper_score ?? 0}%</span></div>
                    <div className="flex justify-between gap-4"><span className="text-slate-400">Report</span><span className="ix-mono font-semibold text-slate-700 truncate">{results.audit?.report_id || '—'}</span></div>
                  </div>
                </div>
              </section>
            ) : (
              <section className="bg-white rounded-xl border border-dashed border-slate-300 p-8 text-center">
                <FileText size={26} strokeWidth={1.5} className="mx-auto text-slate-300 mb-3" />
                <p className="text-sm font-semibold text-slate-600">No inspection yet</p>
                <p className="text-xs text-slate-400 mt-1">Run a document inspection to see extracted fields here.</p>
              </section>
            )}

            <div className="w-full h-[340px] bg-white rounded-xl border border-slate-200/80 shadow-sm flex flex-col items-center justify-center text-slate-400 gap-3">
              <Radar size={28} strokeWidth={1.5} className="text-slate-300" />
              <span className="text-xs ix-mono">daily scan volume — chart placeholder</span>
            </div>
          </main>
        )}

        {/* SCANNER TAB */}
        {currentTab === "scanner" && (
          <main className="space-y-8 print:space-y-6">

            <div className="flex items-center gap-3 print:hidden">
              <label htmlFor="document-type" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Document type
              </label>
              <select
                id="document-type"
                value={documentType}
                onChange={(event) => setDocumentType(event.target.value)}
                className="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm font-medium text-slate-700 shadow-sm"
              >
                <option value="passport">Passport</option>
                <option value="visa">Visa</option>
                <option value="national_id">National ID</option>
                <option value="driving_license">Driving licence</option>
                <option value="permit">Permit</option>
                <option value="aadhaar">Aadhaar Card</option>
                <option value="pan_card">PAN Card</option>
                <option value="college_id">College ID</option>
                <option value="marksheet">Marksheet / Degree</option>
                <option value="voter_id">Voter ID</option>
                <option value="other">Other / Generic</option>
              </select>
            </div>

            {/* Intake bay */}
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-6 items-stretch print:hidden">

              {/* Document slot */}
              <div
                className={`ix-corner ${documentFile ? '' : 'ix-idle'} bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col items-center justify-center min-h-[310px] cursor-pointer hover:border-slate-300 transition-colors`}
                onClick={() => docInputRef.current.click()}
              >
                <div className="ix-c2" />
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-5">01 — document payload</span>
                <input type="file" ref={docInputRef} className="hidden" accept="image/*,application/pdf" onChange={(e) => handleFileChange(e, setDocumentFile, setDocPreview)} />

                {docPreview ? (
                  documentFile?.type === "application/pdf" ? (
                    <div className="w-44 h-56 bg-slate-50 rounded-lg border border-slate-200 flex flex-col items-center justify-center text-slate-600 gap-3">
                      <FileText size={32} strokeWidth={1.5} className="text-teal-600" />
                      <span className="text-xs font-semibold text-slate-700 px-3 text-center truncate max-w-full">{documentFile.name}</span>
                      <span className="text-[10px] ix-mono text-slate-400">pdf document</span>
                    </div>
                  ) : (
                    <img src={docPreview} alt="Document" className="max-h-[220px] rounded border border-slate-200 object-contain shadow-xs" />
                  )
                ) : (
                    <div className="w-44 h-56 rounded-lg border-2 border-dashed border-slate-200 bg-slate-50/50 flex flex-col items-center justify-center text-slate-400 gap-2 hover:bg-slate-50 transition-colors">
                    <Upload size={24} strokeWidth={1.5} className="text-slate-400" />
                      <span className="text-xs font-medium text-slate-500 text-center px-4">Select a document above</span>
                  </div>
                )}
              </div>

              {/* Connector */}
              <div className="hidden lg:flex flex-col items-center justify-center gap-2 px-1">
                <div className={`w-px h-16 ${linked ? 'bg-teal-500' : 'bg-slate-200'} transition-colors`} />
                <div className={`w-9 h-9 rounded-full border flex items-center justify-center transition-colors ${linked ? 'border-teal-500 text-teal-600 bg-teal-50' : 'border-slate-200 text-slate-400 bg-white'}`}>
                  <Link2 size={16} strokeWidth={2} />
                </div>
                <div className={`w-px h-16 ${linked ? 'bg-teal-500' : 'bg-slate-200'} transition-colors`} />
              </div>

              {/* Face slot */}
              <div className={`ix-corner ${liveFaceFile ? '' : 'ix-idle'} bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col items-center justify-center min-h-[310px]`}>
                <div className="ix-c2" />
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-5">02 — facial verification</span>

                <div className="flex-grow flex items-center justify-center">
                  {isWebcamActive ? (
                    <div className="flex flex-col items-center gap-4">
                      <div className="rounded-lg overflow-hidden border-2 border-teal-500 relative shadow-sm">
                        <video ref={videoRef} autoPlay playsInline className="w-44 h-56 object-cover bg-black"></video>
                        <div className="absolute inset-x-2 top-0 h-px bg-teal-400 ix-scanline" />
                      </div>
                      <canvas ref={canvasRef} className="hidden"></canvas>
                      <button onClick={captureWebcam} className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg text-xs font-semibold transition-colors shadow-sm">
                        <Camera size={14} strokeWidth={2.25} /> Capture frame
                      </button>
                    </div>
                  ) : facePreview ? (
                    <div className="cursor-pointer" onClick={() => faceInputRef.current.click()}>
                      <img src={facePreview} alt="Live face" className="w-44 h-56 object-cover rounded-lg border border-teal-500 shadow-xs" />
                    </div>
                  ) : (
                    <div className="w-44 h-56 rounded-lg border-2 border-dashed border-slate-200 bg-slate-50/50 flex flex-col items-center justify-center text-slate-400 gap-2 hover:bg-slate-50 transition-colors">
                      <Camera size={24} strokeWidth={1.5} className="text-slate-400" />
                      <span className="text-xs font-medium text-slate-500 text-center px-4">No image captured</span>
                    </div>
                  )}
                </div>

                {!isWebcamActive && (
                  <div className="flex gap-2 mt-5">
                    <input type="file" ref={faceInputRef} className="hidden" accept="image/*" onChange={(e) => handleFileChange(e, setLiveFaceFile, setFacePreview)} />
                    <button onClick={() => faceInputRef.current.click()} className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors">
                      <Upload size={13} strokeWidth={2} /> Upload
                    </button>
                    <button onClick={startWebcam} className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors">
                      <Camera size={13} strokeWidth={2} /> Camera
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Run action */}
            <div className="flex justify-center print:hidden">
              <button
                onClick={analyzeDocument}
                disabled={isAnalyzing}
                className={`flex items-center gap-2.5 font-bold py-3.5 px-9 rounded-lg text-sm shadow-sm transition-all ${isAnalyzing ? 'bg-slate-200 text-slate-400 cursor-not-allowed' : 'bg-teal-600 hover:bg-teal-700 text-white hover:shadow'}`}
              >
                {isAnalyzing ? (
                  <>
                    <RotateCcw size={17} className="animate-spin" />
                    Running inspection...
                  </>
                ) : (
                  <>
                    <ScanLine size={17} strokeWidth={2.25} />
                    Run inspection
                  </>
                )}
              </button>
            </div>

            {results && (
              <div className="ix-print-report space-y-6">

                <div className="hidden print:block mb-6 border-b border-slate-200 pb-4">
                  <h1 className="ix-display text-2xl font-bold text-slate-900">IdentityX</h1>
                  <p className="text-sm text-slate-500">Inspection report — generated {new Date().toLocaleString()}</p>
                </div>

                <div className="flex justify-between items-center border-b border-slate-200 pb-4 print:hidden">
                  <h2 className="ix-display text-lg font-bold text-slate-900">Inspection report</h2>
                  <button onClick={handlePrint} className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 px-3.5 py-2 rounded-lg hover:bg-slate-50 shadow-xs transition-colors">
                    <Printer size={14} strokeWidth={2} /> Export PDF
                  </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                  {/* Pipeline */}
                  <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Verification pipeline</h3>
                    <div>
                      <PipelineRow label="OCR extraction" ok={results.ocr?.status === 'success'} okText="success" badText="failed" />
                      <PipelineRow label="MRZ consistency" ok={results.validation?.mrz_mismatches?.length === 0} okText="valid / n.a." badText="mismatch" warn />
                      <PipelineRow label="Document integrity" ok={results.validation?.status === 'VALID'} okText="valid" badText="suspicious" warn />
                      <PipelineRow label="Tampering check (ELA)" ok={!results.tampering?.is_tampered} okText="genuine" badText={`${results.tampering?.tamper_score}% suspicious`} />
                      {liveFaceFile && (
                        <PipelineRow label="Biometric face match" ok={Boolean(results.face_match?.match)} okText={`${results.face_match?.similarity}% match`} badText="mismatch" />
                      )}
                    </div>
                  </div>

                  {/* Risk */}
                  <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Calculated risk factor</h3>
                    <div className="flex items-baseline gap-2 mb-3">
                      <span className="ix-display text-5xl font-bold" style={{ color: riskScore > 50 ? '#E11D48' : riskScore > 20 ? '#D97706' : '#0D9488' }}>
                        {riskScore}
                      </span>
                      <span className="text-sm font-semibold text-slate-400">/ 100</span>
                    </div>
                    <Meter value={riskScore ?? 0} />
                    <p className="text-xs font-medium mt-3 text-slate-600">
                      {riskScore > 50 ? 'High risk — recommend manual review' : riskScore > 20 ? 'Medium risk — flagged for attention' : 'Low risk — no material concerns'}
                    </p>

                    {riskScore > 20 && (
                      <div className="mt-5 pt-4 border-t border-slate-100">
                        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Detected anomalies</h4>
                        <ul className="text-xs text-slate-600 space-y-1.5 font-medium">
                          {results.validation?.warnings?.map((warn, i) => <li key={i} className="flex gap-2"><span className="text-slate-400">—</span>{warn}</li>)}
                          {results.validation?.mrz_mismatches?.map((mm, i) => <li key={i} className="flex gap-2"><span className="text-slate-400">—</span>{mm}</li>)}
                          {results.tampering?.is_tampered && <li className="flex gap-2"><span className="text-slate-400">—</span>Visual tampering flags triggered</li>}
                          {results.face_match?.match === false && <li className="flex gap-2"><span className="text-slate-400">—</span>Facial biometric verification failure</li>}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
                    Extracted fields — {documentType.replace('_', ' ')}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
                    {Object.entries(results.ocr?.extracted_fields || {}).map(([field, value]) => (
                      <div key={field} className="flex justify-between gap-4 border-b border-slate-100 pb-2 text-sm">
                        <span className="text-slate-400">{field.replaceAll('_', ' ')}</span>
                        <span className="text-right font-semibold text-slate-700">{value || 'Not detected'}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Heatmap */}
                {results.tampering?.heatmap_image && (
                  <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-rose-600 mb-1">Error level analysis heatmap</h3>
                    <p className="text-xs text-slate-500 mb-4">Highlights density variance suggesting digital editing or composite layers.</p>
                    <img src={results.tampering.heatmap_image} alt="Tampering heatmap" className="w-full max-w-xl mx-auto rounded-lg border border-slate-200" />
                  </div>
                )}

                {/* Audit trail */}
                {results.audit && (
                  <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Blockchain audit trail</h3>
                      <span className="text-xs ix-mono font-semibold text-teal-600 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded">{results.audit.blockchain_status}</span>
                    </div>
                    <div className="ix-mono text-xs text-slate-700 divide-y divide-slate-100">
                      <div className="flex justify-between py-2.5"><span className="text-slate-400">report id</span><span className="truncate ml-4 font-medium">{results.audit.report_id}</span></div>
                      <div className="flex justify-between py-2.5"><span className="text-slate-400">timestamp</span><span className="font-medium">{results.audit.timestamp}</span></div>
                      <div className="flex justify-between py-2.5 gap-4"><span className="text-slate-400 shrink-0">document hash</span><span className="truncate font-medium">{results.audit.document_hash}</span></div>
                      <div className="flex justify-between py-2.5 gap-4"><span className="text-slate-400 shrink-0">transaction id</span><span className="text-teal-600 font-medium truncate">{results.audit.transaction_id}</span></div>
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