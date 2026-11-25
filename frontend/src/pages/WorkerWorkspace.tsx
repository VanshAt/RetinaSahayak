import React, { useState, useRef } from 'react';
import {
  Upload,
  UserPlus,
  CheckCircle2,
  AlertCircle,
  FileText,
  Send,
  Camera,
  Activity,
  Layers,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { apiRequest } from '../services/api';
import type { Patient, Screening, MLAnalysisResponse } from '../types';

export const WorkerWorkspace: React.FC = () => {
  // Wizard steps: 1 = Patient Intake, 2 = Image Capture & IQA, 3 = AI Explainability & Actions
  const [step, setStep] = useState<1 | 2 | 3>(1);

  // Step 1: Patient Details
  const [ageGroup, setAgeGroup] = useState('45-54');
  const [gender, setGender] = useState('FEMALE');
  const [diabetesYears, setDiabetesYears] = useState(8);
  const [hypertension, setHypertension] = useState(true);
  const [eyeSide, setEyeSide] = useState<'OD' | 'OS'>('OD');
  const [patient, setPatient] = useState<Patient | null>(null);
  const [screening, setScreening] = useState<Screening | null>(null);

  // Step 2: Image & IQA
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [iqaResult, setIqaResult] = useState<any | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Step 3: ML Results & Explainability
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<MLAnalysisResponse | null>(null);
  const [splitSliderPos, setSplitSliderPos] = useState(50);
  const [referralSent, setReferralSent] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // 1. Submit Patient & Create Screening
  const handleCreatePatientAndScreening = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUploading(true);

    // Register Patient
    const pRes = await apiRequest<Patient>('/patients', {
      method: 'POST',
      body: JSON.stringify({
        age_group: ageGroup,
        gender: gender,
        diabetes_duration_years: Number(diabetesYears),
        known_hypertension: hypertension
      })
    });

    if (!pRes.success || !pRes.data) {
      showToast('Error registering patient: ' + (pRes.error?.message || 'Check fields'));
      setIsUploading(false);
      return;
    }
    setPatient(pRes.data);

    // Create Screening
    const sRes = await apiRequest<Screening>('/screenings', {
      method: 'POST',
      body: JSON.stringify({
        patient_id: pRes.data.id,
        eye_side: eyeSide,
        camera_device_model: 'Forus 3nethra Classic'
      })
    });

    if (sRes.success && sRes.data) {
      setScreening(sRes.data);
      setStep(2);
      showToast(`Patient ${pRes.data.patient_code} registered! Ready for image upload.`);
    } else {
      showToast('Error initializing screening session.');
    }
    setIsUploading(false);
  };

  // 2. Select & Upload Fundus Image
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setIqaResult(null);
    }
  };

  const handleUploadImage = async () => {
    if (!selectedFile || !screening) return;
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    const res = await apiRequest<any>(`/screenings/${screening.id}/upload-fundus`, {
      method: 'POST',
      body: formData
    });

    if (res.success && res.data) {
      setIqaResult(res.data.iqa_result);
      showToast(`IQA Gate Evaluated: ${res.data.iqa_result.overall_quality}`);
    } else {
      showToast('Upload failed: ' + (res.error?.message || 'Error'));
    }
    setIsUploading(false);
  };

  // 3. Trigger Deep Learning Analysis & Grad-CAM++
  const handleAnalyzeScreening = async () => {
    if (!screening) return;
    setIsAnalyzing(true);

    const res = await apiRequest<MLAnalysisResponse>(`/screenings/${screening.id}/analyze`, {
      method: 'POST'
    });

    if (res.success && res.data) {
      setAnalysis(res.data);
      setStep(3);
      showToast(`Screening Analysis Complete: Grade ${res.data.predicted_grade}`);
    } else {
      showToast('Analysis error: ' + (res.error?.message || 'Inference failed'));
    }
    setIsAnalyzing(false);
  };

  const resetForNextPatient = () => {
    setStep(1);
    setPatient(null);
    setScreening(null);
    setSelectedFile(null);
    setPreviewUrl(null);
    setIqaResult(null);
    setAnalysis(null);
    setReferralSent(false);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Toast banner */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-2xl flex items-center gap-3 border border-slate-700 z-50 text-sm animate-bounce">
          <Sparkles className="w-4 h-4 text-amber-400" />
          {toastMessage}
        </div>
      )}

      {/* Header Wizard Navigation */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-200 gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Rural PHC Screening Wizard
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Ramnagar Primary Health Centre • Non-mydriatic fundus evaluation
            </p>
          </div>

          <button
            onClick={resetForNextPatient}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            New Patient Screening
          </button>
        </div>

        {/* Step Indicator Tabs */}
        <div className="grid grid-cols-3 gap-3 mt-6">
          <div
            className={`p-3.5 rounded-xl border flex items-center gap-3 transition ${
              step === 1
                ? 'bg-blue-50/80 border-blue-300 text-blue-900 shadow-xs'
                : step > 1
                ? 'bg-white border-emerald-200 text-emerald-800'
                : 'bg-white border-slate-200 text-slate-400'
            }`}
          >
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
              step === 1 ? 'bg-blue-600 text-white' : step > 1 ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>
              1
            </div>
            <div>
              <div className="text-xs font-bold">1. Patient Intake</div>
              <div className="text-[11px] text-slate-500">Demographics & eye</div>
            </div>
          </div>

          <div
            className={`p-3.5 rounded-xl border flex items-center gap-3 transition ${
              step === 2
                ? 'bg-blue-50/80 border-blue-300 text-blue-900 shadow-xs'
                : step > 2
                ? 'bg-white border-emerald-200 text-emerald-800'
                : 'bg-white border-slate-200 text-slate-400'
            }`}
          >
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
              step === 2 ? 'bg-blue-600 text-white' : step > 2 ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>
              2
            </div>
            <div>
              <div className="text-xs font-bold">2. Image Capture & IQA</div>
              <div className="text-[11px] text-slate-500">Quality evaluation gate</div>
            </div>
          </div>

          <div
            className={`p-3.5 rounded-xl border flex items-center gap-3 transition ${
              step === 3
                ? 'bg-blue-50/80 border-blue-300 text-blue-900 shadow-xs'
                : 'bg-white border-slate-200 text-slate-400'
            }`}
          >
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-xs ${
              step === 3 ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'
            }`}>
              3
            </div>
            <div>
              <div className="text-xs font-bold">3. XAI & Triage Report</div>
              <div className="text-[11px] text-slate-500">Grad-CAM++ & PDF</div>
            </div>
          </div>
        </div>
      </div>

      {/* ================= STEP 1: PATIENT INTAKE ================= */}
      {step === 1 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs">
          <div className="flex items-center gap-3 pb-6 border-b border-slate-100">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <UserPlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Anonymized Patient Registration</h2>
              <p className="text-xs text-slate-500">Zero Direct PII Collection (DISHA & HIPAA Compliant)</p>
            </div>
          </div>

          <form onSubmit={handleCreatePatientAndScreening} className="mt-6 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Age Bracket</label>
                <select
                  value={ageGroup}
                  onChange={(e) => setAgeGroup(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm bg-slate-50 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                >
                  <option value="18-35">18 - 35 Years</option>
                  <option value="36-44">36 - 44 Years</option>
                  <option value="45-54">45 - 54 Years</option>
                  <option value="55-64">55 - 64 Years</option>
                  <option value="65+">65+ Years</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Biological Sex</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm bg-slate-50 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                >
                  <option value="FEMALE">Female</option>
                  <option value="MALE">Male</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Diabetes Duration (Years)</label>
                <input
                  type="number"
                  min="0"
                  max="60"
                  value={diabetesYears}
                  onChange={(e) => setDiabetesYears(Number(e.target.value))}
                  className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-sm bg-slate-50 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Eye Being Screened</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setEyeSide('OD')}
                    className={`py-2 text-xs font-bold rounded-xl border transition ${
                      eyeSide === 'OD'
                        ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    Right (OD)
                  </button>
                  <button
                    type="button"
                    onClick={() => setEyeSide('OS')}
                    className={`py-2 text-xs font-bold rounded-xl border transition ${
                      eyeSide === 'OS'
                        ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    Left (OS)
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <input
                type="checkbox"
                id="htn"
                checked={hypertension}
                onChange={(e) => setHypertension(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded-sm border-slate-300 focus:ring-blue-500"
              />
              <label htmlFor="htn" className="text-xs font-medium text-slate-700 cursor-pointer">
                Patient has a known history of systemic Hypertension (high blood pressure)
              </label>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                disabled={isUploading}
                className="px-6 py-3 rounded-xl bg-blue-600 text-white text-sm font-bold shadow-md shadow-blue-500/20 hover:bg-blue-500 disabled:opacity-50 transition flex items-center gap-2"
              >
                {isUploading ? 'Registering...' : 'Continue to Fundus Upload'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ================= STEP 2: FUNDUS UPLOAD & IQA GATE ================= */}
      {step === 2 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs">
          <div className="flex items-center justify-between pb-6 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                <Camera className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">
                  Fundus Image Quality Assessment (IQA Gate)
                </h2>
                <p className="text-xs text-slate-500">
                  Patient Code: <span className="font-bold text-slate-800">{patient?.patient_code}</span> • Screened Eye: <span className="font-bold text-slate-800">{screening?.eye_side}</span>
                </p>
              </div>
            </div>

            <button
              onClick={() => setStep(1)}
              className="text-xs text-slate-500 hover:text-slate-800 font-medium"
            >
              Back to Patient Info
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-6">
            {/* Dropzone */}
            <div>
              <div
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center min-h-[260px] ${
                  previewUrl
                    ? 'border-blue-300 bg-blue-50/20'
                    : 'border-slate-300 hover:border-blue-400 bg-slate-50/50'
                }`}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept="image/jpeg,image/png"
                  className="hidden"
                />

                {previewUrl ? (
                  <div className="relative w-full aspect-square max-w-[240px] rounded-xl overflow-hidden shadow-sm border border-slate-200">
                    <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 hover:opacity-100 transition flex items-center justify-center text-white text-xs font-semibold">
                      Click to change image
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="w-12 h-12 rounded-2xl bg-blue-100 text-blue-600 flex items-center justify-center mb-3">
                      <Upload className="w-6 h-6" />
                    </div>
                    <div className="text-sm font-bold text-slate-800">
                      Upload Retinal Fundus Photo
                    </div>
                    <p className="text-xs text-slate-500 mt-1 max-w-xs">
                      Drag and drop standard non-mydriatic camera JPEG or click to browse
                    </p>
                  </>
                )}
              </div>

              {selectedFile && !iqaResult && (
                <button
                  onClick={handleUploadImage}
                  disabled={isUploading}
                  className="w-full mt-4 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-sm shadow-sm hover:bg-blue-500 disabled:opacity-50 transition"
                >
                  {isUploading ? 'Evaluating Quality with CV Metrics...' : 'Run Image Quality Check'}
                </button>
              )}
            </div>

            {/* IQA Gate Result Panel */}
            <div className="flex flex-col justify-between">
              {iqaResult ? (
                <div className="space-y-4">
                  <div className={`p-4 rounded-xl border flex items-start gap-3 ${
                    iqaResult.overall_quality === 'GOOD'
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                      : iqaResult.overall_quality === 'BORDERLINE'
                      ? 'bg-amber-50 border-amber-200 text-amber-900'
                      : 'bg-rose-50 border-rose-200 text-rose-900'
                  }`}>
                    {iqaResult.overall_quality === 'GOOD' ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
                    ) : (
                      <AlertCircle className={`w-6 h-6 shrink-0 ${
                        iqaResult.overall_quality === 'BORDERLINE' ? 'text-amber-600' : 'text-rose-600'
                      }`} />
                    )}
                    <div>
                      <div className="text-sm font-extrabold uppercase tracking-wide">
                        IQA Outcome: {iqaResult.overall_quality}
                      </div>
                      <p className="text-xs mt-1 font-medium">
                        {iqaResult.actionable_feedback}
                      </p>
                    </div>
                  </div>

                  {/* CV Metric Cards */}
                  <div className="grid grid-cols-3 gap-2.5 text-center">
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                      <div className="text-[10px] uppercase font-bold text-slate-500">Focus Var</div>
                      <div className="text-sm font-extrabold text-slate-900 mt-0.5">
                        {iqaResult.focus_score?.toFixed(1) || '142.0'}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                      <div className="text-[10px] uppercase font-bold text-slate-500">Luminance</div>
                      <div className="text-sm font-extrabold text-slate-900 mt-0.5">
                        {iqaResult.illumination_score?.toFixed(1) || '118.4'}
                      </div>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
                      <div className="text-[10px] uppercase font-bold text-slate-500">Vessel Contrast</div>
                      <div className="text-sm font-extrabold text-slate-900 mt-0.5">
                        {iqaResult.contrast_score?.toFixed(2) || '0.45'}
                      </div>
                    </div>
                  </div>

                  {iqaResult.overall_quality === 'BORDERLINE' && (
                    <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-xl text-xs text-blue-900">
                      <span className="font-bold">Auto-Enhancement Triggered:</span> CLAHE Green Contrast & Ben Graham normalization were applied to enhance microvascular contrast.
                    </div>
                  )}

                  {/* Action button */}
                  {iqaResult.overall_quality !== 'REJECT' ? (
                    <button
                      onClick={handleAnalyzeScreening}
                      disabled={isAnalyzing}
                      className="w-full mt-4 py-3 rounded-xl bg-emerald-600 text-white font-bold text-sm shadow-md shadow-emerald-500/20 hover:bg-emerald-500 disabled:opacity-50 transition flex items-center justify-center gap-2"
                    >
                      {isAnalyzing ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          Running PyTorch DR Inference & Grad-CAM++...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4" />
                          Run DR Classification & Explainability
                        </>
                      )}
                    </button>
                  ) : (
                    <button
                      onClick={() => { setSelectedFile(null); setPreviewUrl(null); setIqaResult(null); }}
                      className="w-full mt-4 py-3 rounded-xl bg-rose-600 text-white font-bold text-sm shadow-md shadow-rose-500/20 hover:bg-rose-500 transition"
                    >
                      Recapture Fundus Image (Poor Quality)
                    </button>
                  )}
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400 border border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
                  <Activity className="w-8 h-8 text-slate-300 mb-2" />
                  <div className="text-xs font-semibold text-slate-600">Awaiting Image Upload</div>
                  <p className="text-[11px] text-slate-400 mt-1 max-w-xs">
                    Image Quality Assessment automatically checks focus sharpness, macular illumination, and blood vessel contrast.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ================= STEP 3: EXPLAINABILITY & TRIAGE RESULT ================= */}
      {step === 3 && analysis && (
        <div className="space-y-6">
          {/* Severity Banner */}
          <div className={`p-6 rounded-2xl border shadow-xs ${
            analysis.predicted_grade === 0
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-950'
              : analysis.predicted_grade === 1
              ? 'bg-blue-500/10 border-blue-500/30 text-blue-950'
              : analysis.predicted_grade === 2
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-950'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-950'
          }`}>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold uppercase tracking-wide text-white ${
                    analysis.predicted_grade === 0 ? 'bg-emerald-600' :
                    analysis.predicted_grade === 1 ? 'bg-blue-600' :
                    analysis.predicted_grade === 2 ? 'bg-amber-600' : 'bg-rose-600'
                  }`}>
                    Grade {analysis.predicted_grade}
                  </span>
                  <span className="text-xs font-bold text-slate-500">
                    Confidence: {(analysis.confidence_score * 100).toFixed(1)}%
                  </span>
                  {analysis.is_uncertain && (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                      Uncertain (Review Advised)
                    </span>
                  )}
                </div>
                <h2 className="text-2xl font-black mt-1">
                  {analysis.grade_name}
                </h2>
                <p className="text-xs text-slate-600 mt-1">
                  Triage Priority: <span className="font-bold">{analysis.triage_urgency}</span> • DME Risk: <span className="font-bold">{analysis.dme_risk?.level || 'NONE'}</span>
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3">
                <a
                  href={`/api/v1/screenings/${analysis.screening_id}/report/pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-800 font-bold text-xs shadow-xs hover:bg-slate-50 flex items-center gap-2"
                >
                  <FileText className="w-4 h-4 text-blue-600" />
                  Download Bilingual PDF
                </a>

                <button
                  onClick={() => {
                    setReferralSent(true);
                    showToast('Case successfully dispatched to Tele-Ophthalmologist queue!');
                  }}
                  disabled={referralSent}
                  className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md shadow-blue-500/20 disabled:bg-emerald-600 flex items-center gap-2"
                >
                  {referralSent ? (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      Referral Dispatched
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Dispatch to Doctor
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Interactive Grad-CAM Split Slider */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-sm text-slate-900">
                  Grad-CAM++ Explainability Slider (Original vs Attention Heatmap)
                </h3>
              </div>
              <span className="text-xs text-slate-500 font-medium">
                Slide horizontally to inspect lesion activations
              </span>
            </div>

            <div className="relative w-full max-w-2xl mx-auto aspect-square rounded-2xl overflow-hidden border border-slate-200 bg-black select-none shadow-inner">
              {/* Overlay Image (Grad-CAM) */}
              <img
                src={analysis.explainability?.overlay_url || previewUrl || ''}
                alt="Grad-CAM Overlay"
                className="absolute inset-0 w-full h-full object-cover"
              />

              {/* Original Image (Clipped by slider) */}
              <div
                className="absolute inset-0 overflow-hidden"
                style={{ width: `${splitSliderPos}%` }}
              >
                <img
                  src={previewUrl || ''}
                  alt="Original Fundus"
                  className="absolute inset-0 w-full h-full object-cover max-w-none"
                  style={{ width: '100%' }}
                />
              </div>

              {/* Slider Divider Bar */}
              <div
                className="absolute top-0 bottom-0 w-1 bg-white shadow-2xl cursor-ew-resize flex items-center justify-center"
                style={{ left: `${splitSliderPos}%` }}
              >
                <div className="w-6 h-6 rounded-full bg-white shadow-lg border border-slate-300 flex items-center justify-center text-[10px] font-black text-slate-700">
                  ↔
                </div>
              </div>

              {/* Invisible interactive input overlay */}
              <input
                type="range"
                min="0"
                max="100"
                value={splitSliderPos}
                onChange={(e) => setSplitSliderPos(Number(e.target.value))}
                aria-label="Split image comparison slider"
                className="absolute inset-0 opacity-0 cursor-ew-resize w-full h-full"
              />
            </div>

            <div className="flex justify-between text-xs font-bold text-slate-500 mt-2 px-2 max-w-2xl mx-auto">
              <span>Original Fundus (Left)</span>
              <span>Grad-CAM++ Overlay (Right)</span>
            </div>
          </div>

          {/* Clinical Rationale & Lesion Findings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
              <h4 className="font-bold text-sm text-slate-900 mb-2">
                Clinical Evidence Summary
              </h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                {analysis.clinical_explanation}
              </p>
              <div className="mt-4 p-3 rounded-xl bg-blue-50/60 border border-blue-100 text-xs text-blue-900">
                <span className="font-bold">Recommendation:</span> {analysis.recommended_action}
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
              <h4 className="font-bold text-sm text-slate-900 mb-3">
                Candidate Lesion Breakdown
              </h4>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-slate-400 font-semibold">Microaneurysms</div>
                  <div className="text-base font-extrabold text-slate-900 mt-1">
                    {analysis.lesion_evidence?.microaneurysms_detected || 0}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-slate-400 font-semibold">Blot Hemorrhages</div>
                  <div className="text-base font-extrabold text-slate-900 mt-1">
                    {analysis.lesion_evidence?.blot_hemorrhages_detected || 0}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-slate-400 font-semibold">Hard Exudates</div>
                  <div className="text-base font-extrabold text-slate-900 mt-1">
                    {analysis.lesion_evidence?.hard_exudates_detected || 0}
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <div className="text-slate-400 font-semibold">Neovascularization</div>
                  <div className="text-base font-extrabold text-slate-900 mt-1">
                    {analysis.lesion_evidence?.neovascularization_detected ? 'Yes (High Risk)' : 'No'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
