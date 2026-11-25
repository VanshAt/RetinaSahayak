import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  ArrowUpRight,
  ShieldCheck,
  Clock,
  Sparkles
} from 'lucide-react';
import { apiRequest } from '../services/api';
import type { Referral } from '../types';

export const DoctorCockpit: React.FC = () => {
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [selectedReferral, setSelectedReferral] = useState<Referral | null>(null);
  const [loading, setLoading] = useState(true);

  // Diagnostic Canvas State
  const [zoomLevel, setZoomLevel] = useState(1);
  const [filterMode, setFilterMode] = useState<'NATURAL' | 'RED_FREE' | 'CLAHE'>('NATURAL');
  const [heatmapOpacity, setHeatmapOpacity] = useState(40);

  // Clinical Review Form State
  const [decisionType, setDecisionType] = useState('AGREE_WITH_AI');
  const [confirmedGrade, setConfirmedGrade] = useState<number>(2);
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadReferrals = async () => {
    setLoading(true);
    const res = await apiRequest<{ items: Referral[]; total: number }>('/referrals');
    if (res.success && res.data) {
      setReferrals(res.data.items);
      if (res.data.items.length > 0 && !selectedReferral) {
        setSelectedReferral(res.data.items[0]);
        setConfirmedGrade(res.data.items[0].predicted_grade);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    loadReferrals();
  }, []);

  const handleSelectCase = (ref: Referral) => {
    setSelectedReferral(ref);
    setConfirmedGrade(ref.predicted_grade);
    setZoomLevel(1);
    setFilterMode('NATURAL');
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReferral) return;
    setIsSubmitting(true);

    const res = await apiRequest('/reviews', {
      method: 'POST',
      body: JSON.stringify({
        screening_id: selectedReferral.screening_id,
        decision_type: decisionType,
        confirmed_grade: Number(confirmedGrade),
        clinical_status: confirmedGrade >= 2 ? 'REFERRED_TERTIARY' : 'CASE_CLOSED',
        clinical_notes: clinicalNotes || 'Verified microvascular findings via deep zoom inspection.',
        doctor_digital_signature: 'Dr. Verma MBBS MS Ophthalmology'
      })
    });

    if (res.success) {
      showToast(`Review officially signed off with SHA-256 digital signature!`);
      loadReferrals();
    } else {
      showToast('Error recording review: ' + (res.error?.message || 'Failed'));
    }
    setIsSubmitting(false);
  };

  const handleEscalateCase = async () => {
    if (!selectedReferral) return;
    const res = await apiRequest(`/referrals/${selectedReferral.id}/escalate`, {
      method: 'POST',
      body: JSON.stringify({
        target_hospital_name: 'Regional Institute of Ophthalmology, BHU',
        escalation_reason: 'Emergency sight-threatening neovascularization'
      })
    });
    if (res.success) {
      showToast('Case successfully escalated to tertiary hospital emergency queue!');
      loadReferrals();
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Toast banner */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 bg-slate-900 text-white px-5 py-3 rounded-xl shadow-2xl flex items-center gap-3 border border-slate-700 z-50 text-sm animate-bounce">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          {toastMessage}
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-200 mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <Stethoscope className="w-6 h-6 text-blue-600" />
            Tele-Ophthalmologist Verification Cockpit
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            District Tertiary Eye Care Unit • Prioritized Clinical Referral Queue
          </p>
        </div>

        <button
          onClick={loadReferrals}
          className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-xs flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Refresh Queue
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* ================= LEFT: REFERRAL QUEUE ================= */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden flex flex-col h-[750px]">
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Active Referrals ({referrals.length})
            </span>
            <span className="text-[11px] font-semibold text-slate-400">
              Ranked by Urgency
            </span>
          </div>

          <div className="overflow-y-auto flex-1 divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">
                Loading referral queue...
              </div>
            ) : referrals.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No pending referrals in queue.
              </div>
            ) : (
              referrals.map((ref) => {
                const isSelected = selectedReferral?.id === ref.id;
                return (
                  <div
                    key={ref.id}
                    onClick={() => handleSelectCase(ref)}
                    className={`p-4 cursor-pointer transition text-left ${
                      isSelected
                        ? 'bg-blue-50/80 border-l-4 border-l-blue-600'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wide text-white ${
                          ref.clinical_priority === 'EMERGENCY' ? 'bg-rose-600' :
                          ref.clinical_priority === 'URGENT' ? 'bg-amber-600' :
                          ref.clinical_priority === 'UNCERTAIN_REVIEW' ? 'bg-purple-600' : 'bg-blue-600'
                        }`}>
                          {ref.clinical_priority}
                        </span>
                        <span className="text-xs font-bold text-slate-900">
                          {ref.patient_code}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 flex items-center gap-1 font-medium">
                        <Clock className="w-3 h-3" />
                        {new Date(ref.dispatched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <div className="mt-2 text-xs text-slate-600">
                      <span className="font-semibold text-slate-800">Grade {ref.predicted_grade} DR</span> • Eye: {ref.eye_side} • {ref.age_group}/{ref.gender}
                    </div>

                    <div className="text-[11px] text-slate-400 mt-0.5">
                      PHC: {ref.phc_name}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* ================= RIGHT: DEEP-ZOOM DIAGNOSTIC VIEWER & REVIEW FORM ================= */}
        <div className="lg:col-span-8 space-y-6">
          {selectedReferral ? (
            <>
              {/* Diagnostic Canvas */}
              <div className="bg-slate-900 rounded-2xl p-4 shadow-xl border border-slate-800 text-white">
                <div className="flex flex-wrap items-center justify-between pb-3 border-b border-slate-800 gap-3">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm">{selectedReferral.patient_code}</span>
                    <span className="text-xs text-slate-400">({selectedReferral.eye_side})</span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                      Grade {selectedReferral.predicted_grade} (Confidence: {(selectedReferral.confidence_score * 100).toFixed(1)}%)
                    </span>
                  </div>

                  {/* Filter & Opacity Controls */}
                  <div className="flex items-center gap-2 text-xs">
                    <div className="flex bg-slate-800 p-0.5 rounded-lg border border-slate-700">
                      <button
                        onClick={() => setFilterMode('NATURAL')}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
                          filterMode === 'NATURAL' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Natural
                      </button>
                      <button
                        onClick={() => setFilterMode('RED_FREE')}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
                          filterMode === 'RED_FREE' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Red-Free (Green)
                      </button>
                      <button
                        onClick={() => setFilterMode('CLAHE')}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
                          filterMode === 'CLAHE' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Enhanced
                      </button>
                    </div>

                    <div className="flex items-center gap-1.5 bg-slate-800 px-2 py-1 rounded-lg border border-slate-700">
                      <span className="text-[10px] text-slate-400">Grad-CAM:</span>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={heatmapOpacity}
                        onChange={(e) => setHeatmapOpacity(Number(e.target.value))}
                        aria-label="Grad-CAM heatmap opacity"
                        className="w-16 accent-blue-500 cursor-pointer"
                      />
                      <span className="text-[10px] text-slate-300 w-6 font-mono">{heatmapOpacity}%</span>
                    </div>

                    {/* Zoom Buttons */}
                    <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700">
                      <button
                        onClick={() => setZoomLevel((prev) => Math.min(prev + 0.25, 3))}
                        title="Zoom In"
                        className="p-1 text-slate-400 hover:text-white"
                      >
                        <ZoomIn className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setZoomLevel((prev) => Math.max(prev - 0.25, 1))}
                        title="Zoom Out"
                        className="p-1 text-slate-400 hover:text-white"
                      >
                        <ZoomOut className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setZoomLevel(1)}
                        title="Reset View"
                        className="p-1 text-slate-400 hover:text-white"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Deep Zoom Canvas Area */}
                <div className="relative w-full aspect-16/9 rounded-xl overflow-hidden bg-black mt-3 flex items-center justify-center">
                  <div
                    className="relative transition-transform duration-150 ease-out"
                    style={{
                      transform: `scale(${zoomLevel})`,
                      filter:
                        filterMode === 'RED_FREE'
                          ? 'sepia(1) hue-rotate(80deg) saturate(2)'
                          : filterMode === 'CLAHE'
                          ? 'contrast(1.4) brightness(1.05)'
                          : 'none'
                    }}
                  >
                    <img
                      src={selectedReferral.original_image_url || ''}
                      alt="Base Fundus"
                      className="max-h-[380px] object-contain rounded-lg"
                    />

                    {selectedReferral.heatmap_url && heatmapOpacity > 0 && (
                      <img
                        src={selectedReferral.heatmap_url}
                        alt="Grad-CAM Heatmap"
                        className="absolute inset-0 w-full h-full object-contain rounded-lg pointer-events-none mix-blend-screen"
                        style={{ opacity: heatmapOpacity / 100 }}
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* Review & Sign-Off Form */}
              <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-emerald-600" />
                    <h3 className="font-bold text-sm text-slate-900">
                      Ophthalmologist Clinical Verification & Cryptographic Sign-Off
                    </h3>
                  </div>

                  <button
                    onClick={handleEscalateCase}
                    type="button"
                    className="text-xs font-bold text-rose-600 hover:text-rose-700 flex items-center gap-1 bg-rose-50 px-2.5 py-1.5 rounded-lg border border-rose-200"
                  >
                    <ArrowUpRight className="w-3.5 h-3.5" />
                    Escalate to Emergency Unit
                  </button>
                </div>

                <form onSubmit={handleSubmitReview} className="mt-5 space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Doctor Decision Type
                      </label>
                      <select
                        value={decisionType}
                        onChange={(e) => setDecisionType(e.target.value)}
                        className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs bg-slate-50 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                      >
                        <option value="AGREE_WITH_AI">Agree with AI Assessment</option>
                        <option value="MODIFY_GRADE">Modify Severity Grade</option>
                        <option value="MARK_NON_REFERABLE">Mark Non-Referable (Normal)</option>
                        <option value="REQUEST_REPEAT_IMAGING">Request Repeat Imaging</option>
                        <option value="MARK_FOLLOW_UP_REQUIRED">Routine 3-Month Follow Up</option>
                        <option value="CLOSE_CASE">Close Case</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Confirmed DR Grade (0 to 4)
                      </label>
                      <select
                        value={confirmedGrade}
                        onChange={(e) => setConfirmedGrade(Number(e.target.value))}
                        className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs bg-slate-50 font-bold focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                      >
                        <option value={0}>Grade 0 — No Diabetic Retinopathy</option>
                        <option value={1}>Grade 1 — Mild Non-Proliferative DR</option>
                        <option value={2}>Grade 2 — Moderate Non-Proliferative DR</option>
                        <option value={3}>Grade 3 — Severe Non-Proliferative DR</option>
                        <option value={4}>Grade 4 — Proliferative DR (Sight-Threatening)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Specialist Clinical Notes & Treatment Recommendation
                    </label>
                    <textarea
                      rows={2}
                      value={clinicalNotes}
                      onChange={(e) => setClinicalNotes(e.target.value)}
                      placeholder="e.g. Microaneurysms confirmed in inferior-temporal arcade. Focal laser photocoagulation recommended within 4 weeks."
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs bg-slate-50 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                    />
                  </div>

                  <div className="pt-2 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400 font-mono">
                      Security: SHA-256 Chained Digital Signature
                    </span>

                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-500/20 disabled:opacity-50 transition flex items-center gap-2"
                    >
                      <CheckCircle className="w-4 h-4" />
                      {isSubmitting ? 'Recording Signature...' : 'Submit Verification & Sign-Off'}
                    </button>
                  </div>
                </form>
              </div>
            </>
          ) : (
            <div className="h-96 flex flex-col items-center justify-center bg-white rounded-2xl border border-slate-200 text-slate-400 p-8 text-center">
              <AlertTriangle className="w-10 h-10 text-slate-300 mb-2" />
              <div className="text-sm font-bold text-slate-700">Select a Referral Case</div>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Choose an item from the triage queue on the left to examine high-resolution fundus images and Grad-CAM++ lesion heatmaps.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
